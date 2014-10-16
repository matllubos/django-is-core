

class SaveObjectException(Exception):
    
    def __unicode__(self):
        return self.message
