#!/usr/bin/python

from nbs_api import API
import json
from datetime import timedelta
from datetime import datetime
import urllib
import pickle
import random
import time
import collections
daysBeforeRelease = 15
training_set_size = 20
services_used = set(["MySpace", "Last.fm", "Facebook", "Twitter", "YouTube", "Wikipedia"])

# I have an artist name and the albums I want to get metrics for
# for each album, get metrics of the artist according to album release date

def get_artist_map_from_pickle(filename):
  artist_to_albums = pickle.load(open('artist_to_albums.pickle', 'rb'))
  # random_artist_names = random.sample(artist_to_albums.keys(), training_set_size)
  random_artist_names = ["Earl Sweatshirt"]

  reduced_artist_to_albums = {}
  for artist_name in random_artist_names:
    reduced_artist_to_albums[artist_name] = artist_to_albums[artist_name]

  print "album listing" + str(reduced_artist_to_albums)

  return reduced_artist_to_albums

def get_artist_to_release_dates_map(artist_to_albums):
  artist_to_releases = {}
  for artist, albumMap in artist_to_albums.iteritems():
    # Iterate through all albums to get a list of release dates
    album_map = {}
    for album_name, album_tuple in albumMap.iteritems():
      curr_release_date = (album_tuple[0])
      album_map[album_name] = curr_release_date

    artist_to_releases[artist] = album_map

  # map with keys being artist names and value being a map (album_name:relaseDate)
  return artist_to_releases

def remove_firs_and_last_line(jsonStr):
  jsonStr = jsonStr[:jsonStr.rfind(']') + 1]
  jsonStr = jsonStr[jsonStr.find('\n'):]
  print "fixed json: " + jsonStr
  print "json end"
  return jsonStr

def get_metrics_object(api, artistId, options):
  albumMetricsJson = api.metricsArtist(artistId, options)
  print albumMetricsJson
  currAlbumMetrics = None

  try:
    currAlbumMetrics = json.loads(albumMetricsJson)
  except ValueError:
    print "removing first and last line"
    albumMetricsJson = remove_firs_and_last_line(albumMetricsJson)
    currAlbumMetrics = json.loads(albumMetricsJson)

  return currAlbumMetrics

def get_artist_id(api, target_artist_name):
  try: 
    map_of_artists = json.loads(api.artistSearch(target_artist_name))
    print str(map_of_artists)
    # Loop through each key in artistMaps and only select the one with the exact string match
    # Perhaps also check that those artists have the album names we have
    # print map_of_artists
    artist_id = None
    # get the artist NSB id number

    for curr_artist_id, data_map in map_of_artists.iteritems():
      if data_map['name'] == target_artist_name:
        artist_id = curr_artist_id
        # print "The NBS ID is " + artist_id
        # print "The artist name is " + data_map['name']
    return artist_id
  except TypeError:
    print "error in getting id"
    return -1

def create_vectors_from_albums(api, artist_id, album_releases_map): 
  # Now get the metrics for this artist according to each album
  albums_to_vectors_map = {}
  for album_name, release_date_obj in album_releases_map.iteritems():
    print album_name
    print str(release_date_obj)
    datetime_release = datetime(release_date_obj.year, release_date_obj.month, release_date_obj.day)
    end_time = int(time.mktime(datetime_release.timetuple()))
    # get a range a certain amount of days before the release
    start_time = int(end_time - (timedelta(days = daysBeforeRelease).total_seconds()))
    print "start time: " + str(start_time) + " " + str(datetime.fromtimestamp(start_time))
    print "end time: " + str(end_time) + " " + str(datetime.fromtimestamp(end_time))

    start_param = urllib.urlencode({'start': str(start_time)})
    end_param = urllib.urlencode({'end': str(end_time)})
    metrics_param = urllib.urlencode({'metric': 'all'})


    options = [str(start_time), str(end_time), 'all']

    
    print "option: "  + str(options)
    print "artist_id: " + str(artist_id)

    curr_album_metrics = get_metrics_object(api, artist_id, options)
    curr_album_feature_vector = metrics_to_vector(curr_album_metrics)

    if curr_album_feature_vector != None:
     albums_to_vectors_map[album_name] = curr_album_feature_vector

  return albums_to_vectors_map

def get_feature_vector_for_a_service(metric_map):
  # then calculate the values
  # Iterate through the metric map and compute the range and average values for each cateogry
  metric_vector = []
  for metric_type, item_to_count_map in metric_map.iteritems():

    difference_feature = 0
    average_feature = 0

    # process all the items we have here
    # get the difference feature

    if type(item_to_count_map) is dict and len(item_to_count_map) > 0:
      item_to_count_map = collections.OrderedDict(sorted(item_to_count_map.items()))
      sorted_keys = item_to_count_map.keys()
      print "sorted keys: " + str(sorted_keys)
      print "map: " + str(item_to_count_map)

      if len(sorted_keys) > 1:
        difference_feature = item_to_count_map[sorted_keys[-1]] - item_to_count_map[sorted_keys[0]]
      else:
        difference_feature = item_to_count_map[sorted_keys[0]]

      #average feature
      running_sum = 0
      for item_id, count_value in item_to_count_map.iteritems():
        running_sum += count_value
      average_feature = running_sum / len(sorted_keys)

    metric_vector.append(difference_feature)
    metric_vector.append(average_feature)

  # add our two features to the vector
  print "difference: " + str(difference_feature)
  print "average: " + str(average_feature)
  return metric_vector

#album stats will be raw counts example
#{'Facebook': {likes: ...., counts...}}
def metrics_to_vector(album_metrics):
  print "Converting stats to vectors"
  feature_map = {}
  final_vector = []
  total_services_used = 0

  # for every Service in the metrics map
  for service_map in album_metrics:
    service_name = service_map['Service']['name']
    metric_map = service_map['Metric']

    # If an artist has no YouTube data, then trash it
    if (service_name == "YouTube" and len(metric_map['plays']) == 0):
      print "Trashing"
      print service_name
      print str(metric_map)
      return None

    if (service_name in services_used) and metric_map != None:
      service_vector = get_feature_vector_for_a_service(metric_map)
      feature_map[service_name] = service_vector

  if len(feature_map) != len(services_used):
    return None
  else:
    # Convert a feature map to the final vector
    for service_str in services_used:
      final_vector = final_vector + feature_map[service_str]


    print "vector size: " + str(len(final_vector))
    return final_vector

  #   album_stats_map[service_name] = metric_map

  # return album_stats_map


  # album_vectors = {}
  # for album_name, album_stat_map:
  #   for service_name, 

def generate_training_data(artists_to_release_dates):
  api = API("Pedrostanford")
  # album_releases_map is a map from album name to release date
  all_albums_to_vectors = {}
  for artist_name, album_releases_map in artists_to_release_dates.iteritems():
    curr_artist_id = get_artist_id(api, artist_name)
    # if we got the id, then continue processing
    if curr_artist_id != -1 and curr_artist_id != None:
      single_artists_album_vectors = create_vectors_from_albums(api, curr_artist_id, album_releases_map)
      # add these album:vectors map to our total map
      all_albums_to_vectors.update(single_artists_album_vectors)
  

  print "Finished generating training features!!!!!!!!! " + str(all_albums_to_vectors)

print ">> Running our metrics scrapper..."
artist_to_albums = get_artist_map_from_pickle('artist_to_albums.pickle')
artists_to_release_dates = get_artist_to_release_dates_map(artist_to_albums)
generate_training_data(artists_to_release_dates)