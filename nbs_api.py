from lib.factory import ResourceFactory

class API:

  def __init__(self,key,ext,secret):
    self.factory = ResourceFactory(key,ext,secret)

  def artist(self):
    return self.factory.getArtists( )

  def artistView(self,id):
    return self.artist().view(id)

  def artistSearch(self,name):
    return self.artist( ).search(name)

  def artistRanking(self,type,ids):
    return self.artist().rank(type,ids)

  def artistAdd(self,name, profiles):
    return self.artist().add(name, profiles)

  def genres(self):
    return self.factory.getGenres()

  def genresArtist(self,id):
    return self.genres().artist(id)

  def metrics(self):
    return self.factory.getMetrics()

  def metricsProfile(self, id, opt=[]):
    return self.metrics().profile(id, opt)

  def metricsArtist(self, id, opt=[]):
    return self.metrics().artist(id, opt)

  def profiles(self):
    return self.factory.getProfiles()

  def profilesArtist(self, id):
    return self.profiles().artist(id)

  def profilesSearch(self, url):
    return self.profiles().search(url)

  def profilesAdd(self, id, profiles):
    return self.profiles().add(id, profiles)

  def services(self):
    return self.factory.getServices()

  def servicesList(self):
    return self.services().list()

