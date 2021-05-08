#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
import datetime
from flask import (
  Flask, 
  render_template, 
  jsonify, 
  request, 
  Response, 
  flash, 
  redirect, 
  url_for
)
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  # Array needed to sort the venues by state 
  data = []
  for location in Venue.query.distinct(Venue.state, Venue.city):
    venues_data = []
    venues = Venue.query.filter(Venue.state == location.state, Venue.city == location.city).with_entities(Venue.id, Venue.name)
    for venue in venues:
      num_upcoming_shows = Show.query.filter(Show.venue_id == venue.id, Show.start_time > datetime.datetime.now()).count()    
      venues_data.append({"id": venue.id, "name": venue.name, "num_upcoming_shows": num_upcoming_shows})

    data.append({"city": location.city, "state": location.state, "venues": venues_data})

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term')
  search_results_data = []
  search_results = Venue.query.filter(Venue.name.ilike('%' + search_term +'%')).with_entities(Venue.id, Venue.name)
  for result in search_results:
    num_upcoming_shows = Show.query.filter(Show.venue_id == result.id, Show.start_time > datetime.datetime.now()).count()    
    
    search_results_data.append({"id": result.id, "name": result.name, "num_upcoming_shows": num_upcoming_shows})
  
  response={
    "count": len(search_results_data),
    "data": search_results_data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # DONE: replace with real venue data from the venues table, using venue_id
  # d = Venue.query(Venue).join(Venue.shows)
  data = Venue.query.first_or_404(venue_id)

  upcoming_shows = []
  past_shows = []

  for show in data.shows:
    upcoming = datetime.datetime.now() < show.start_time
    show.start_time = format_datetime(str(show.start_time))
    show.artist_image_link = show.artist_shows.image_link
    show.artist_name = show.artist_shows.name
    if upcoming:
      upcoming_shows.append(show)
    else:
      past_shows.append(show)
  
    setattr(data, 'upcoming_shows', upcoming_shows)
    setattr(data, 'past_shows', past_shows)
    setattr(data, 'upcoming_shows_count', len(upcoming_shows))
    setattr(data, 'past_shows_count', len(past_shows))
  else:
    data = Venue.query.get(venue_id)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  if not form.validate_on_submit():
      flash(form.errors)
      return render_template('forms/new_venue.html', form=form)
  # DONE: insert form data as a new Venue record in the db, instead
  try:
    newVenue = Venue(
      name = form.name.data, 
      city = form.city.data, 
      state = form.state.data,
      address = form.address.data, 
      phone = form.phone.data, 
      genres = form.genres.data, 
      facebook_link = form.facebook_link.data, 
      image_link = form.image_link.data, 
      website = form.website_link.data, 
      seeking_description = form.seeking_description.data, 
      seeking_talent = form.seeking_talent.data
    )
    db.session.add(newVenue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  finally:
    db.session.close()
    return redirect(url_for('index'))

  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  print(venue_id)
  try:
    venue = Venue.query.filter_by(id = venue_id).delete()
    db.session.commit()
    flash('Venue was successfully deleted!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue could not be deleted.')
  finally:
    db.session.close()
    return jsonify({'success': True})
  
  return redirect(url_for('index'))
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # DONE: replace with real data returned from querying the database
  data = Artist.query.with_entities(Artist.id, Artist.name)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  search_result = Artist.query.filter(Artist.name.ilike('%' + search_term +'%')).with_entities(Artist.id, Artist.name)
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": search_result.count(),
    "data": search_result
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # DONE: replace with real artist data from the artist table, using artist_id
  data = Artist.query.get(artist_id)

  upcoming_shows = []
  past_shows = []

  for show in data.shows:
    upcoming = datetime.datetime.now() < show.start_time
    show.start_time = format_datetime(str(show.start_time))
    show.venue_image_link = show.venue_shows.image_link
    show.venue_name = show.venue_shows.name
    if upcoming:
      upcoming_shows.append(show)
    else:
      past_shows.append(show)
  
  setattr(data, 'upcoming_shows', upcoming_shows)
  setattr(data, 'past_shows', past_shows)
  setattr(data, 'upcoming_shows_count', len(upcoming_shows))
  setattr(data, 'past_shows_count', len(past_shows))
  return render_template('pages/show_artist.html', artist=data)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
  if not form.validate_on_submit():
    flash(form.errors)
    return render_template('forms/new_artist.html', form=form)
  try:
    newArtist = Artist(
      name = form.name.data, 
      city = form.city.data, 
      state = form.state.data,
      phone = form.phone.data, 
      genres = form.genres.data, 
      facebook_link = form.facebook_link.data, 
      image_link = form.image_link.data, 
      website = form.website_link.data, 
      seeking_description = form.seeking_description.data, 
      seeking_venue = form.seeking_venue.data
    )
    db.session.add(newArtist)

    # Using flush to preserve the Id created to be used in redirect
    db.session.flush()
    new_artist_id = newArtist.id

    db.session.commit()
    
    flash('Artist ' + form.name.data + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
  finally:
    db.session.close()
    return redirect(url_for('show_artist', artist_id=new_artist_id))

  # called upon submitting the new artist listing form
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  form.name.default = artist.name
  form.city.default = artist.city
  form.state.default = artist.state
  form.phone.default = artist.phone
  form.genres.default = artist.genres
  form.facebook_link.default = artist.facebook_link
  form.image_link.default = artist.image_link
  form.website_link.default = artist.website
  form.seeking_venue.checked = artist.seeking_venue
  form.seeking_description.default = artist.seeking_description
  
  form.process()
  # DONE: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  try:
    form = ArtistForm()
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = form.genres.data
    artist.facebook_link = form.facebook_link.data, 
    artist.image_link = form.image_link.data, 
    artist.website = form.website_link.data, 
    artist.seeking_venue = form.seeking_venue.data
    if form.seeking_venue.data:
      artist.seeking_description = form.seeking_description.data
    else:
      artist.seeking_description = ''

    db.session.commit()
    flash(form.name.data + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. ' + form.name.data + ' could not be updated.')
  finally:
    db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

  # DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  form.name.default = venue.name
  form.city.default = venue.city
  form.state.default = venue.state
  form.address.default = venue.address
  form.phone.default = venue.phone
  form.genres.default = venue.genres
  form.facebook_link.default = venue.facebook_link
  form.image_link.default = venue.image_link
  form.website_link.default = venue.website
  form.seeking_talent.checked = venue.seeking_talent
  form.seeking_description.default = venue.seeking_description

  form.process()
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  try:
    form = VenueForm()
    venue.name = form.name.data 
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data 
    venue.phone = form.phone.data
    venue.genres = form.genres.data 
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    if form.seeking_talent.data:
      venue.seeking_description = form.seeking_description.data,
    else:
      venue.seeking_description = ''
    
    db.session.commit()
    flash(form.name.data + ' was successfully updated!')

  except:
    db.session.rollback()
    flash('An error occurred. ' + form.name.data + ' could not be updated.')
  finally:
    db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = Show.query.all()
  upcoming_shows = []
  past_shows = []

  for show in shows:
    upcoming = datetime.datetime.now() < show.start_time
    show.start_time = format_datetime(str(show.start_time))
    show.venue_name = show.venue_shows.name
    show.artist_image_link = show.artist_shows.image_link
    show.artist_name = show.artist_shows.name
    if upcoming:
      upcoming_shows.append(show)
    else:
      past_shows.append(show)
    
  return render_template('pages/shows.html', shows=upcoming_shows, past_shows=past_shows)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    form = ShowForm()
    newShow = Show(
      artist_id = form.artist_id.data,
      venue_id = form.venue_id.data,
      start_time = form.start_time.data
    )
    db.session.add(newShow)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
    return render_template('pages/home.html')
  # called to create new shows in the db, upon submitting new show listing form
  # DONE: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  
  # DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
