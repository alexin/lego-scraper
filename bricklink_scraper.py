#!/usr/bin/python

import bs4
import csv
import errno
import os
import shutil
import sys
import urllib2

def sanitized (s) :
  return s.replace(unichr(160), " ").strip()

def merge_items_into (dst, src) :
  n_merges = 0
  for item_id in src :
    # merges item
    if dst.has_key(item_id) :
      dst[item_id][0] += src[item_id][0] # quantities are summed up
      n_merges += 1;

    # adds item
    else :
      dst[item_id] = src[item_id]

  return n_merges

def count_total_quantity (items) :
  total = 0
  for item in items.values() :
    total += item[0]
  return total

def row_has_strings (row, strings) :
  columns = row.find_all('td')
  if len(columns) != len(strings) :
    return False
  for i in range(0, len(columns)) :
    s = sanitized(columns[i].string)
    if s != strings[i] :
      return False
  return True

def find_items_table (soup) :
  tables = soup.find_all("table", class_="ta")
  headers = ['Image', 'Qty', 'Item No', 'Description', 'MID']
  for table in tables :
    if row_has_strings(table.tr, headers) :
      return table
  return None

def is_part_row (row) :
  bgcolor = row['bgcolor']
  return bgcolor == '#EEEEEE' or bgcolor == '#FFFFFF'

def scrape_part_row (row, items) :
  columns = row.find_all('td')
  part = sanitized(columns[2].a.string)
  name = sanitized(columns[3].b.string)
  image = sanitized(columns[0].b.a.img['src'])
  quantity = int(sanitized(columns[1].string))

  # On one hand, the part number is not unique, because the same part may come
  # in various colors. On the other hand, the name differentiates between colors
  # but seems too prone to spelling errors. Therefore, the key is the part
  # number and name combined.
  item_id = (part, name)

  if items.has_key(item_id) :
    print "Duplicated item: "+str(item_id)

  else :
    items[item_id] = [quantity, '=IMAGE("'+image+'")', part, name]

def scrape_items_table (table) :
  rows = table.find_all('tr', recursive=False)
  n_rows = len(rows);
  i = 0

  # Advances to the regular items.
  while i < n_rows and not row_has_strings(rows[i], ['Regular Items:']) :
    i += 1;
  i += 2 # skip headers

  # REGUALR ITEMS
  regular_items = {}
  while i < n_rows and is_part_row(rows[i]) :
    scrape_part_row(rows[i], regular_items)
    i += 1
  print '  Regular items:'
  print '    Parts: '+str(len(regular_items))
  print '    Quantity: '+str(count_total_quantity(regular_items))

  # Advances to the extra items.
  while i < n_rows and not row_has_strings(rows[i], ['Extra Items:']) :
    i += 1;
  i += 2; # skip headers

  # EXTRA ITEM
  extra_items = {}
  while i < n_rows and is_part_row(rows[i]) :
    scrape_part_row(rows[i], extra_items)
    i += 1
  print '  Extra items:'
  print '    Parts: '+str(len(extra_items))
  print '    Quantity: '+str(count_total_quantity(extra_items))

  n_merges = merge_items_into(regular_items, extra_items)
  print '  Extra items merged: '+str(n_merges)

  return regular_items # all items

def scrape_model (model) :
  page = urllib2.urlopen('https://www.bricklink.com/catalogItemInv.asp?S='+model+'-1')
  soup = bs4.BeautifulSoup(page, "html.parser")
  table = find_items_table(soup)
  items = {}
  if table != None :
    print 'Scraping model '+model+'...'
    items = scrape_items_table(table)
  return items

def write_items (file, items) :
  with open(file, 'w') as fp:
    a = csv.writer(fp, delimiter=',')
    # Order by name.
    items_list = sorted(items.values(), key=lambda item: item[3])
    a.writerows(items_list)

def ensure_path_exists (path) :
  try :
    os.makedirs(path)
  except OSError as exception :
    if exception.errno != errno.EEXIST :
      raise

def main () :
  # Results are saved in a specific folder.
  ensure_path_exists(os.path.join(os.getcwd(), 'out'))

  two_or_more_models = len(sys.argv) > 2

  if two_or_more_models :
    # Creates a folder named after each model.
    foldername = '_'.join(sys.argv[1:])
    folderpath = os.path.join(os.getcwd(), 'out', foldername)
    if os.path.exists(folderpath) :
      shutil.rmtree(folderpath)
    ensure_path_exists(folderpath)

  all_items = {} # Aggregates all items from all models.

  # Scrapes and saves a file for each model.
  for i in range(1, len(sys.argv)) :
    model = sys.argv[i]
    items = scrape_model(model)

    if two_or_more_models :
      file = os.path.join('out', foldername, model+'.csv')
    else : # One model only.
      file = os.path.join('out', model+'.csv')
    write_items(file, items)

    n_merges = merge_items_into(all_items, items)

  # Prints some statistics.
  print 'Total items:'
  print '  Total parts: '+str(len(all_items))
  print '  Total quantity: '+str(count_total_quantity(all_items))
  if len(sys.argv) > 2 : # Two or more models.
    print '  Items merged: '+str(n_merges)

  # Saves a file that aggregates the results from each model.
  if two_or_more_models :
    file = os.path.join('out', foldername, 'all.csv')
    write_items(file, all_items)

if __name__ == "__main__" :
  main()
