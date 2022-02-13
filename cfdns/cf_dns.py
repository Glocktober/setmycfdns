import os
import CloudFlare

DEBUGCF=os.environ.get('DEBUGCF',False)


class CFzone:
    """ CloudFlare dns zone """

    def __init__(self, cf_domain, ):

        self._domain = cf_domain
        self._cf = CloudFlare.CloudFlare(debug=DEBUGCF)

        zone_info = self.get_zoneid(cf_domain)
        if not zone_info:
            emes = f'Can\'t Find a CloudFlare zone for {cf_domain}'
            raise Exception(emes)
        self.zoneid = zone_info['id']
        self.zonename = zone_info['name']


    def get_zoneid(self,fqdn):
        """ From the fqdn find the CloudFlare zone id """

        fparts = fqdn.split('.')
        while(fparts):
            r = self._cf.zones.get(params={'match':'all', 'name': '.'.join(fparts)})
            if len(r) == 1:
                return r[0]
            fparts = fparts[1:]
        return None        


    def create(self,params):
        """ Add a record, return the record id """

        r = self._cf.zones.dns_records.post(self.zoneid, data=params)        
        return r['id']


    def get(self,params={}):
        """ Get a record """

        r = self._cf.zones.dns_records.get(self.zoneid,params=params)
        return r


    def getid(self,params={}):
        """ Return a specific record id """

        r = self.get(params)
        recs = len(r)
        if recs == 1:
            return r[0]['id']
        elif recs == 0:
            return 0
        else:
            raise Exception('Multiple records found') 


    def set(self,rid,params={}):
        """ Set (update) a specific record id """

        r = self._cf.zones.dns_records.put(self.zoneid, rid, data=params)

        return r['id']        


    def delete(self,rid):
        """ Delete a DNS record """

        r = self._cf.zones.dns_records.delete(self.zoneid, rid)
        return r['id']



class CFrec:
    """ CloudFlare DNS record abstraction """
    
    def __init__(self, domain, type='A'):

        self.type = type
        self.zone = CFzone(domain)
        self.zonename = self.zone.zonename


    def update(self, name, contents, addok=False):
        """ set (update or create) record """

        fqdn = name if name.endswith(self.zonename) else f'{name}.{self.zonename}'

        rid = self.zone.getid({'name':fqdn,'type': self.type, 'match': 'all'})
        if rid:
            # update record
            return self.zone.set(rid,{'name': fqdn, 'type': self.type, 'content': contents})
        elif addok:
            # doesn't exist be we can create a new record
            return self.zone.create({'name': fqdn, 'type': self.type, 'content': contents})
        else:
            # doesn't exist
            return None
    

    def add(self, name, contents):
        """ Add a new record """

        fqdn = name if name.endswith(self.zonename) else f'{name}.{self.zonename}'

        return self.zone.create({'name': fqdn, 'type': self.type, 'content': contents})
        

    def get(self, name):
        """ get contents of record """

        fqdn = name if name.endswith(self.zonename) else f'{name}.{self.zonename}'

        r =  self.zone.get({'name': fqdn, 'type': self.type, 'match': 'all'})

        recs = len(r)
        if recs == 1:
            return r[0]['content']
        elif recs == 0:
            return None
        else:
            raise Exception("Multiple records found")


    def rem(self, name):
        """ remove a TXT record """

        fqdn = name if name.endswith(self.zonename) else f'{name}.{self.zonename}'

        rid = self.zone.getid({'name':fqdn,'type': self.type, 'match': 'all'})
        if rid:
            # remove the record
            return self.zone.delete(rid)
        else:
            # couldn't find the record
            return False
    

class TXTrec(CFrec):
    """ CF TXT Record """

    def __init__(self, domain):
        
        super().__init__(domain, 'TXT')
    

class Arec(CFrec):
    """ CF A ipv4 Record """

    def __init__(self, domain):
        
        super().__init__(domain, 'A')


class CNAMErec(CFrec):
    """ CF CNAME Record """

    def __init__(self, domain):
        
        super().__init__(domain, 'CNAME')


class AAAArec(CFrec):
    """ CF AAAA ipv6 Record """

    def __init__(self, domain):
        
        super().__init__(domain, 'AAAA')

