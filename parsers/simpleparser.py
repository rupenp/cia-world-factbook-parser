#!/usr/bin/env python
"""
Version 1 - Simple Parser
"""
__author__ = 'Rupen'
__email__ = 'rupen@cs.vt.edu'
__version__ = "0.0.1"

import os
import glob
import base64
import ujson as json
from bs4 import BeautifulSoup

def _image(link, base_dir):
    try:
        with open(os.path.join(base_dir, link.img.__dict__['attrs']['src']), "rb") as imageFile:
            return base64.b64encode(imageFile.read())
    except:
        return None
    
def _country_description(soup, base_dir):
    co_desc_fields = [u'countryaffiliation', u'countrycode', u'countryname',
                      u'name', u'region', u'regioncode']

    try:
        img_dict = soup.find('a', title="Click flag for description").img.__dict__
    except: 
        try:
            img_dict = soup.find('a', title="Click locator to enlarge").img.__dict__
        except:
            img_dict = soup.find('a', title="Click map to enlarge").img.__dict__

    co_desc_info = {k:img_dict['attrs'].get(k, None) for k in co_desc_fields}
    
    try:
        flag_dict = soup.find('a', title="Click flag for description").img.__dict__
        co_flag_info_fields = [u'flagdescription', u'flagdescriptionnote', u'flagsubfield']
        co_flag_info = {k:flag_dict['attrs'].get(k, None) for k in co_flag_info_fields}
        co_flag_info[u'flag_img_base64'] = _image(soup.find('a', title="Click flag for description"), base_dir)
        co_desc_info[u'flag_info'] = co_flag_info
    except:
        co_desc_info[u'flag_info'] = None
         
    co_maps = {
        'co_locator_img_base64': _image(
            soup.find('a', title="Click locator to enlarge"), base_dir),
        'co_map_img_base64':  _image(
            soup.find('a', title="Click map to enlarge"), base_dir)
        }
    
    co_desc_info[u'map_info'] = co_maps
    return co_desc_info

def _get_category_data_info(category_data):
    subcategories = category_data.find_all('div', class_='category')
    if subcategories:
        subcategories_data = []
        for subcategory in subcategories:
            subcategories_data.append(
                {'sub_category_name': subcategory.next.strip().replace(":",""),
                 'sub_category_data': subcategory.span.text.strip()})
        return subcategories_data
    else:
        return category_data.find('div', class_='category_data').text.strip()

def _get_all_categories(soup, regioncode, ccode):
    categories = {}
    for category in soup.find_all(class_=regioncode + '_light'):
        info = {
            'category_name': category.find('a').text.strip().replace(":",""),
            'category_data': _get_category_data_info(category.fetchNextSiblings('tr')[0].find(id='data')),
            'section_title': category.fetchParents('div')[0]
                        .fetchParents('div', class_='answer')[0]
                        .fetchPrevious('h2', ccode=ccode)[0]['sectiontitle']
        }
        
        if info['section_title'] not in categories:
            categories[info['section_title']] = []
        categories[info['section_title']].append(info)
    return categories

def _country_facts(soup, base_dir):
    facts = _country_description(soup, base_dir)
    facts['sections'] = _get_all_categories(soup, facts['regioncode'], facts['countrycode'])
    return facts

if __name__ == '__main__':
    import sys
    import glob
    import codecs
    import argparse
    
    ap = argparse.ArgumentParser()
    ap.add_argument('--factbook-dir', required=True, type=str, help='factbook dir')
    ap.add_argument('--outfile', required=True, type=str, help='out filename')
    args = ap.parse_args()
    
    base_dir = os.path.join(args.factbook_dir,"geos")
    countries_html_files = glob.glob(base_dir + "/*.html")
    print "Number of country files %d" % len(countries_html_files)

    with codecs.open(args.outfile, 'w', encoding='utf8') as out:
        for country_file in countries_html_files:
            soup = BeautifulSoup(open(country_file).read(), 'html.parser')
            facts = _country_facts(soup, base_dir)
            out.write(json.dumps(facts)+'\n')
        