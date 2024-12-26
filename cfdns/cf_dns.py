copyright='gunville 2024'
import os
from pathlib import Path
import cloudflare
import tomllib

DEBUGCF=os.environ.get('DEBUGCF',False)

class Zone_entry:
    def __init__(self,name, id):
        self.name = name
        self.id = id

class CFzone:
    """ CloudFlare dns zone """

    def __init__(self, cf_domain, ):
        api_email = os.environ.get('CLOUDFLARE_EMAIL')
        api_key = os.environ.get('CLOUDFLARE_API_KEY')
        api_token = os.environ.get('CLOUDFLARE_API_TOKEN')
        cf_file = Path('.cloudflare.cf')
        
        if (not cf_file.exists()):
            cf_file = Path.home().joinpath(cf_file)
        
        if (cf_file.exists()):
            with open(cf_file, 'rb') as f:
                auth_data = tomllib.load(f)
                if ('CloudFlare' in auth_data):
                    api_email = auth_data['CloudFlare'].get('email', None)
                    api_key = auth_data['CloudFlare'].get('api_key', None)
                    api_token = auth_data['CloudFlare'].get('api_token', None)
        
        self._domain = cf_domain
        self._cf = cloudflare.Cloudflare(api_email=api_email, api_key=api_key, api_token=api_token)

        self._all_zones = self.get_all_zones()
        
        zone_info = self.get_zoneid(cf_domain)
        if not zone_info:
            emes = f'Can\'t Find a CloudFlare zone for {cf_domain} - maybe the wrong account'
            raise Exception(emes)
        self.zoneid = zone_info.id
        self.zonename = zone_info.name
        

    def get_all_zones(self):
        """ load all zones for account """
        r = self._cf.zones.list()
        all_zones = []
        for res in r.result:
            all_zones.append(Zone_entry(name=res.name, id=res.id))        
        return all_zones


    def get_zoneid(self,fqdn):
        """ From the fqdn find the CloudFlare zone id """

        fparts = fqdn.split('.')
        while(fparts):
            zname = '.'.join(fparts)
            for z in self._all_zones:
                if zname == z.name:
                    return z
            fparts = fparts[1:]
        return None        


    def create(self,**params):
        """ Add a record, return the record id """

        r = self._cf.dns.records.create(zone_id=self.zoneid, **params)        
        
        return r


    def get(self,**args):
        """ Get a record """

        r = self._cf.dns.records.list(zone_id=self.zoneid, **args)
        return r


    def set(self,rid,**kwargs):
        """ Set (update) a specific record id """

        r = self._cf.dns.records.update(zone_id=self.zoneid, dns_record_id=rid, **kwargs)
        
        return r.id


    def delete(self,rid):
        """ Delete a DNS record """

        r = self._cf.dns.records.delete(zone_id=self.zoneid, dns_record_id=rid)
        
        return r.id



class CFrec:
    """ CloudFlare DNS record abstraction """
    
    def __init__(self, domain, type='A'):

        self.type = type
        self.zone = CFzone(domain)
        self.zonename = self.zone.zonename
        self.record = None


    def update(self, name, contents, addok=False):
        """ set (update or create) record """

        fqdn = name if name.endswith(self.zonename) else f'{name}.{self.zonename}'

        if self.record:
            rid = self.record.id
            # update record
            return self.zone.set(rid, name=fqdn, type=self.type, content=contents)
        elif addok:
            # doesn't exist be we can create a new record
            return self.zone.create(name=fqdn, type=self.type, content=contents)
        else:
            # doesn't exist
            return None
    

    def add(self, name, contents):
        """ Add a new record """

        fqdn = name if name.endswith(self.zonename) else f'{name}.{self.zonename}'

        return self.zone.create(name=fqdn, type=self.type, content=contents)
    

    def get(self, name):
        """ get contents of record """

        fqdn = name if name.endswith(self.zonename) else f'{name}.{self.zonename}'
        
        r =  self.zone.get( name=fqdn, type=self.type, match ='all')

        recs = len(r.result)
        if recs == 1:
            self.record = r.result[0]
            return r.result[0].content
        elif recs == 0:
            return None
        else:
            raise Exception("Multiple records found")

        
    def rem(self, name):
        """ remove a TXT record """

        fqdn = name if name.endswith(self.zonename) else f'{name}.{self.zonename}'

        rid = self.record.id
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

