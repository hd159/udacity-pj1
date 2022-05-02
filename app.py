#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from email.utils import localtime
from enum import unique
from functools import reduce
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, session, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler, error
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import UniqueConstraint, func, true

from util import createArtistEntity, createShowArtist, createShowVenue, createVenueEntity, reduceVenues

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
# moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique = True, nullable=False)
    genres = db.Column(db.String, nullable=False)
    address = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    image_link = db.Column(db.String(500))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
db.create_all()
class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique = True, nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    image_link = db.Column(db.String(500))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
db.create_all()
class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)

    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete="cascade"),
                         nullable=False)
    venue = db.relationship('Venue', cascade = "all,delete", backref=db.backref('venue', lazy=True, passive_deletes=True))

    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete="cascade"),
                          nullable=False)
    artist = db.relationship('Artist', cascade = "all,delete", backref=db.backref('artist', lazy=True, passive_deletes=True))
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#
db.create_all()

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    recentVenues = Venue.query.with_entities(Venue.name, Venue.city, Venue.state, Venue.id).order_by(Venue.id.desc()).limit(10).all()
    recentArtists  = Artist.query.with_entities(Artist.name, Artist.id).order_by(Artist.id.desc()).limit(10).all()
    return render_template('pages/home.html', venues = recentVenues, artists = recentArtists)

#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    result  = db.session.query().with_entities(Venue.name, Venue.city, Venue.state, Venue.id).all()
    for venue in result:
        val = dict(venue)
        val['num_upcoming_shows'] = Show.query.filter((Show.venue_id == venue.id) & (Show.start_time >= datetime.now())).count()
        data.append(val)
    venues = list(reduce(reduceVenues, data, []))
    return render_template('pages/venues.html', areas=venues)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response = {
        'count': 0,
        'data': []
    }
    
    search_term=request.form.get('search_term', '')
    filterByname = func.lower(Venue.name).contains(func.lower(search_term))
    filterBycity = func.lower(Venue.city).contains(func.lower(search_term))
    filterByState = func.lower(Venue.state).contains(func.lower(search_term))

    venue =  Venue.query.filter(filterByname | filterBycity | filterByState).with_entities(Venue.id, Venue.name).all()
    for v in venue:
        num_upcoming_shows = Show.query.filter((Show.venue_id == v.id) & (Show.start_time >= datetime.now())).count()
        data = {
            "id": v.id,
            "name": v.name,
            "num_upcoming_shows": num_upcoming_shows
        }
        response["data"].append(data)
        
    response["count"] = len(venue)
    return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    venue.genres = json.loads(venue.genres)
    venue.past_shows = []
    venue.upcoming_shows = []
    past_shows  = db.session.query(Venue, Show).select_from(Show).join(Venue).filter(venue.id == Show.venue_id, Show.start_time < datetime.now()).all()
    upcoming_shows  = db.session.query(Venue, Show).select_from(Show).join(Venue).filter(venue.id == Show.venue_id, Show.start_time >= datetime.now()).all()
    ps_shows = createShowVenue(past_shows)
    up_shows = createShowVenue(upcoming_shows)
    venue.past_shows.extend(ps_shows)
    venue.upcoming_shows.extend(up_shows)
    venue.past_shows_count = len(ps_shows)
    venue.upcoming_shows_count = len(up_shows)

    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    formData = VenueForm(request.form).data
    venue = Venue()
    venue = createVenueEntity(dict(formData), venue)
    try:
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Venue ' + venue.name + ' could not be listed.')

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    flash('Venue ' + venue.name + ' was successfully deleted!')
    return render_template('pages/home.html')



#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.with_entities(Artist.id, Artist.name).all()
    
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        'count': 0,
        'data': []
    }
    
    search_term = request.form.get('search_term', '')
    filterByname = func.lower(Artist.name).contains(func.lower(search_term))
    filterBycity = func.lower(Artist.city).contains(func.lower(search_term))
    filterByState = func.lower(Artist.state).contains(func.lower(search_term))

    artists =  Artist.query.filter(filterByname | filterBycity | filterByState).with_entities(Artist.id, Artist.name).all()
    for artist in artists:
        num_upcoming_shows = Show.query.filter((Show.artist_id == artist.id) & (Show.start_time >= datetime.now())).count()
        data = {
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming_shows
        }
        response["data"].append(data)
        
    response["count"] = len(artists)
    
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)
    artist.genres = json.loads(artist.genres)
    artist.past_shows = []
    artist.upcoming_shows = []
    past_shows  = db.session.query(Artist, Show).select_from(Show).join(Artist).filter(artist.id == Show.artist_id, Show.start_time < datetime.now()).all()
    upcoming_shows  = db.session.query(Artist, Show).select_from(Show).join(Artist).filter(artist.id == Show.artist_id, Show.start_time >= datetime.now()).all()
    ps_shows = createShowArtist(past_shows)
    up_shows = createShowArtist(upcoming_shows)
    artist.past_shows.extend(ps_shows)
    artist.upcoming_shows.extend(up_shows)
    artist.past_shows_count = len(ps_shows)
    artist.upcoming_shows_count = len(up_shows)
   
    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    result = Artist.query.get(artist_id)
    result.genres = json.loads(result.genres)
    
    # TODO: populate form with fields from artist with ID <artist_id>
    form.name.data = result.name
    form.genres.data = result.genres
    form.city.data = result.city
    form.state.data = result.state
    form.phone.data = result.phone
    form.website_link.data = result.website
    form.facebook_link.data = result.facebook_link
    form.seeking_venue.data = result.seeking_venue
    form.seeking_description.data = result.seeking_description
    form.image_link.data = result.image_link
    return render_template('forms/edit_artist.html', form=form, artist=result)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    formData = ArtistForm(request.form).data
    artist = Artist.query.get(artist_id)
    artist = createArtistEntity(dict(formData), artist)
    db.session.commit()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    result = Venue.query.get(venue_id)
    result.genres = json.loads(result.genres)
    # TODO: populate form with values from venue with ID <venue_id>
    form.name.data = result.name
    form.genres.data = result.genres
    form.address.data = result.address
    form.city.data = result.city
    form.state.data = result.state
    form.phone.data = result.phone
    form.website_link.data = result.website
    form.facebook_link.data = result.facebook_link
    form.seeking_talent.data = result.seeking_talent
    form.seeking_description.data = result.seeking_description
    form.image_link.data = result.image_link
    return render_template('forms/edit_venue.html', form=form, venue=result)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    formData = VenueForm(request.form).data
    venue = Venue.query.get(venue_id)
    venue = createVenueEntity(dict(formData), venue)
    db.session.commit()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    formData = ArtistForm(request.form).data
    artist = Artist()
    artist = createArtistEntity(dict(formData), artist)
   
    try:
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception  as e:
        db.session.rollback()
        flash('An error occurred. Artist ' + artist.name + ' could not be listed.')

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = []
    result  = db.session.query(Show, Artist, Venue).join(Artist,Show.artist_id==Artist.id).join(Venue, Show.venue_id==Venue.id).all()
    for row in result:
        res = {}
        res['artist_id'] = row['Show'].artist_id
        res['artist_name'] = row['Artist'].name
        res['artist_image_link'] = row['Artist'].image_link
        res['venue_id'] = row['Show'].venue_id
        res['venue_name'] = row['Venue'].name
        res['start_time'] = row['Show'].start_time.strftime("%b %d %Y ")
        data.append(res)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    formData = ShowForm(request.form).data
    show = Show()
    show.artist_id = formData['artist_id']
    show.venue_id = formData['venue_id']
    show.start_time = formData['start_time']

    try:
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except Exception  as e:
        db.session.rollback()
        flash('An error occurred. Show  could not be listed.')

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
