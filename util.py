import json

def reduceVenues(acc, item):
    findItem = list(filter(lambda x: x['state'] == item['state'] and x['city'] == item['city'] , acc))
    if(len(findItem) == 0):
        newItem = {
            'state': item['state'],
            'city': item['city'],
            'venues': [item]
        }
        acc.append(newItem)
    else:
        findItem[0]['venues'].append(item)
    return acc

def createVenueEntity(data: dict, venue):
    venue.name = data['name']
    venue.city = data['city']
    venue.state = data['state']
    venue.address = data['address']
    venue.phone = data['phone']
    venue.image_link = data['image_link']
    venue.genres = json.dumps(data['genres'])
    venue.facebook_link = data['facebook_link']
    venue.website = data['website_link']
    venue.seeking_talent = data['seeking_talent']
    venue.seeking_description = data['seeking_description']
    return venue

def createArtistEntity(data: dict, artist):
    artist.name = data['name']
    artist.city = data['city']
    artist.state = data['state']
    artist.phone = data['phone']
    artist.image_link = data['image_link']
    artist.genres = json.dumps(data['genres'])
    artist.facebook_link = data['facebook_link']
    artist.website = data['website_link']
    artist.seeking_venue = data['seeking_venue']
    artist.seeking_description = data['seeking_description']
    return artist


def createShowVenue(shows):
    result = []
    for show in shows:
        artist = show.Show.artist
        result.append(
            {
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show.Show.start_time.strftime("%b %d %Y ")
            }
        )
    return result

def createShowArtist(shows):
    result = []
    for show in shows:
        venue = show.Show.venue
        result.append(
            {
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": show.Show.start_time.strftime("%b %d %Y ")
            }
        )
    return result