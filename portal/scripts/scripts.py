# -*- coding: utf-8 -*-
import psycopg2 as psy
import cloudinary as cloud
import cloudinary.api as cloud_api
import os

from scripts.postgres import SELECT, INSERT, UPDATE, DELETE

# Photo upload config
cloud.config(
        cloud_name=os.environ['CLOUDINARY_NAME'],
        api_key=os.environ['CLOUDINARY_KEY'],
        api_secret=os.environ['CLOUDINARY_SECRET']
        )

def handle_new_item(form, files):
    """
    Creates a new product.
    Adds photos to Cloudinary, then inserts a new row in the database with provided metadata and
    URLs to the uploaded photos

    Parameters
    ----------
    form : dict
        The cleaned form containing metadata
    files : list
        The photos to upload to Cloudinary
    """

    # Upload primary photo
    photo_primary = form['photo_primary'].read()
    photo_primary_url = cloud.uploader.upload(photo_primary, folder='againstthegrain')['secure_url']

    # Upload images to cloudinary and form a list of the results
    photo_urls = []
    if files:
        for f in files:
            img = f.read()
            photo_urls.append(cloud.uploader.upload(img, folder='againstthegrain')['secure_url'])

    # Prepare DB insertion
    if form['price'] == None:
        price = -1 # Not for sale
    else:
        price = float(form['price'])

    description = form['description'].replace("'", '').replace('"', '') # Remove quotations so no issues occur during the SQL execution

    # Insert into DB
    INSERT('item', vals=f"DEFAULT, '{form['title']}', '{description}', {price}, '{photo_primary_url}', ARRAY{photo_urls}::character varying[]")

def handle_edit_item(item_id, form):
    """
    Handles changes made to the metadata of a product

    Parameters
    ----------
    item_id : int
        The ID of the item to edit
    vals : str, list
        The cleaned form with the new values
    """

    # Construct UPDATE query
    cols, vals = 'name, price', f"'{form['title']}', {form['price']}"
    if form['description']:
        cols += ', description'
        vals += f", '{form['description']}'"
    if form['photo_primary']:
        # Update the primary photo
        photo_primary = form['photo_primary'].read()
        photo_primary_url = cloud.uploader.upload(photo_primary, folder='template')['secure_url']

        cols += ', photo_primary'
        vals += f", '{photo_primary_url}'"

    UPDATE('item', where=f'id = {item_id}', cols=cols, vals=vals)

def handle_photo_edit(item, deleted_photos, new_photos):
    """
    Handles changes made to the photos of a product

    Parameters
    ----------
    item : dict
        A dict representing the item to update
    deleted_photos : list
        The URLS of the photos to delete
    new _photos : list
        Byte objects of the photos to upload
    """

    # Get a list of the current photo URLs
    cur_photos = item['photos']

    # Delete selected photos
    if deleted_photos:
        for photo in deleted_photos:
            cur_photos.remove(photo)

    # Upload added photos
    if new_photos:
        for photo in new_photos:
            img = photo.read()
            cur_photos.append(cloud.uploader.upload(img, folder='againstthegrain')['secure_url'])

    UPDATE('item', where=f"id = {item['id']}", cols='photos',
                                 vals=f'ARRAY{cur_photos}::character varying[]')
