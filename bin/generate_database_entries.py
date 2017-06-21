#!/usr/bin/env python
"""
This module is a command-line utility that writes to the SQLite database that
is used for lookup of documentation entries.
"""
import argparse
import logging
import multiprocessing
import os
import sqlite3
import time
from bs4 import BeautifulSoup
from lib import chunk


def clean_database(database_file_path):
    """This clears the database of current search entries."""
    logger = logging.getLogger(__name__)
    logger.debug('Making connection to database...')
    conn = sqlite3.connect(database_file_path)
    cur = conn.cursor()

    try:
        logger.debug('Cleaning database...')
        cur.execute('DROP TABLE searchIndex;')
    except:
        logger.warning('Failed to clear out searchIndex! Is this the first time creating the database?')
    finally:
        cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
        cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')


def write_entries(database_file_path,
                  filenames, 
                  docs_sources, 
                  max_version='2017', 
                  timeout=120.0,
                  job_id=0):
    """This function writes search entries to the database."""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('write_entries_{0}'.format(job_id))
    conn = sqlite3.connect(database_file_path, timeout=timeout)
    cur = conn.cursor()
    for f in filenames:
        if os.path.splitext(f)[-1] == '.html':
            if '-members' in f:
                continue
            if f.startswith('class_'):
                logger.debug('Processing: {0}...'.format(f))
                class_name = ''
                name_items = os.path.splitext(f)[0][6:].split('_')
                for idx, section in enumerate(name_items):
                    if section:
                        class_name += section[0].upper() + section[1:]
                    else:
                        if not name_items[idx+1]:
                            class_name += '_'
                
                logger.debug('Inserting class_name: {0}'.format(class_name))
                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                        ' VALUES (\'{name}\', \'Class\', \'{path}\')'.format(name=class_name, path=f))

                # Now start finding items within the class pages to add
                # additional entries for
                html = open(os.path.join(docs_sources, f)).read()
                soup = BeautifulSoup(html, 'html.parser')

                for h2 in soup.find_all('h2', {'class': 'groupheader'}):
                    # Now find all public types defined in the class and create
                    # links to them
                    if h2.a and h2.a.get('name') == 'pub-types':
                        items = h2.parent.parent.parent.find_all(
                            'td',
                            {'class' : 'memItemRight'}
                        )
                        # Do not consider inherited types
                        for pub_type_item in items:
                            if 'el' not in pub_type_item.a.get('class'):
                                continue
                            if 'inherit' in pub_type_item.parent.get('class'):
                                continue
                            type_name = pub_type_item.a.string
                            type_url = pub_type_item.a.get('href')

                            if max_version == '2017':
                                type_url = type_url.replace('#!/url=./cpp_ref/', '')
                            if type_name and type_url:
                                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                                        ' VALUES (\'{class_name}::{type_name}\', \'Type\', \'{path}\')'
                                        .format(class_name=class_name, type_name=type_name, path=type_url))
                    elif h2.a and h2.a.get('name') == 'pub-methods':
                        pub_methods = h2.parent.parent.parent.find_all(
                            'td',
                            {'class' : 'memItemRight'}
                        )
                        # Do not consider inherited functions
                        for m in pub_methods:
                            if 'el' not in m.a.get('class'):
                                continue
                            if 'inherit' in m.parent.get('class'):
                                continue
                            method_name = m.a.string
                            method_url = m.a.get('href')
                            # NOTE: For Maya 2017, it seems the URL is
                            # formatted differently
                            if max_version == '2017':
                                method_url = method_url.replace('#!/url=./cpp_ref/', '')
                            if method_name and method_url:
                                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                                        ' VALUES (\'{class_name}::{method_name}\', \'Method\', \'{path}\')'
                                        .format(class_name=class_name,
                                                method_name=method_name,
                                                path=method_url))
                    elif h2.a and h2.a.get('name') == 'pub-static-methods':
                        pub_methods = h2.parent.parent.parent.find_all(
                            'td',
                            {'class' : 'memItemRight'}
                        )
                        # Do not consider inherited functions
                        for m in pub_methods:
                            if 'el' not in m.a.get('class'):
                                continue
                            if 'inherit' in m.parent.get('class'):
                                continue
                            method_name = m.a.string
                            method_url = m.a.get('href')
                            # NOTE: For Maya 2017, it seems the URL is
                            # formatted differently
                            if max_version == '2017':
                                method_url = method_url.replace('#!/url=./cpp_ref/', '')
                            if method_name and method_url:
                                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                                        ' VALUES (\'{class_name}::{method_name}\', \'Function\', \'{path}\')'
                                        .format(class_name=class_name,
                                                method_name=method_name,
                                                path=method_url))
                    elif h2.a and h2.a.get('name') == 'pro-methods':
                        pub_methods = h2.parent.parent.parent.find_all(
                            'td',
                            {'class' : 'memItemRight'}
                        )
                        # Do not consider inherited functions
                        for m in pub_methods:
                            if 'el' not in m.a.get('class'):
                                continue
                            method_name = m.a.string
                            method_url = m.a.get('href')
                            if method_name and method_url:
                                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                                        ' VALUES (\'{class_name}::{method_name}\', \'Method\', \'{path}\')'
                                        .format(class_name=class_name,
                                                method_name=method_name,
                                                path=method_url))


            elif f.startswith('struct_'):
                struct_name = ''.join([a[0].upper() + a[1:] for a in os.path.splitext(f)[0].split('struct_')[-1].split('_') if a])
                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                        ' VALUES (\'{name}\', \'Struct\', \'{path}\')'.format(name=struct_name, path=f))

            elif f.startswith('namespace'):
                namespace_name = ''.join([a[0].upper() + a[1:] for a in os.path.splitext(f)[0].replace('namespace', '').split('_') if a])
                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                        ' VALUES (\'{name}\', \'Namespace\', \'{path}\')'.format(name=namespace_name, path=f))

            elif '-example' in f:
                example_name = ''.join([a[0].upper() + a[1:] for a in os.path.splitext(f)[0].split('-example')[0].split('_') if a]) + 'Example'
                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                        ' VALUES (\'{name}\', \'Sample\', \'{path}\')'.format(name=example_name, path=f))
            # NOTE (sonictk): Header file documentation
            elif f.endswith('_8h.html'):
                header_name = ''.join([a[0].upper() + a[1:] for a in f[0:-8].split('_') if a])
                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                        ' VALUES (\'{name}\', \'File\', \'{path}\')'.format(name=header_name, path=f))
            elif f.startswith('group___'):
                module_name = ' '.join([a[0].upper() + a[1:] for a in f[8:-5].split('_') if a])
                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                        ' VALUES (\'{name}\', \'Module\', \'{path}\')'.format(name=module_name, path=f))
            elif f.startswith('union_'):
                union_name = ''.join([a[0].upper() + a[1:] for a in f[6:-5].split('_') if a])
                cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path)'
                        ' VALUES (\'{name}\', \'Union\', \'{path}\')'.format(name=union_name, path=f))

    try: conn.commit()
    except sqlite3.OperationalError:
        logger.warning('Encountered database lock, attemping again after 5 seconds...')
        time.sleep(5)
        conn.commit()
    finally:
        logger.debug('Job {0} complete, closing connection to database...'.format(os.getpid()))
        conn.close()


def main(docs_sources, output_path, max_version='2017', multi_thread=False):
    """
    This is the main entry point of the program.
    
    :param docs_sources: ``str`` path to the formatted documentation sources. This 
        should be the root of the folder that contains the ``index.html`` formatted 
        documentation.

    :param output_path: ``str`` path to write the docset database to.

    :param multi_thread: ``bool`` to indicate if multithreading support should be 
        enabled.

    :param max_version: ``str`` indicating what version of 3ds max the docset database
        being generated for is.
    """
    logger = logging.getLogger(__name__)
    database_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                      'max-{0}-cpp.docset'.format(max_version),
                                      'Contents',
                                      'Resources',
                                      'docSet.dsidx')
    if not os.path.isfile(database_file_path):
        logger.debug('The database file: {0} does not exist, creating it...'.format(database_file_path))
        open(database_file_path, 'w').close()
    # Clean the database of existing entries
    clean_database(database_file_path)
    # Write entries
    if not docs_sources:
        docs_sources = os.path.join(os.path.dirname(database_file_path), 'Documents')

    if not os.path.isdir(docs_sources):
        raise IOError('The documentation directory: {0} does not exist!'.format(docs_sources))

    logger.debug('Inserting entries into database...')
    all_files = os.listdir(docs_sources)
    logger.debug('Total number of files to process: {0}'.format(len(all_files)))

    if multi_thread:
        jobs = []
        for idx, s in enumerate(chunk(all_files, 500)):
            job = multiprocessing.Process(target=write_entries,
                    args=(database_file_path, s, docs_sources, max_version, idx))
            jobs.append(job)

        logger.debug('Num. of jobs scheduled: {0}'.format(len(jobs)))
        [j.start() for j in jobs]
        logger.info('Jobs submitted, please wait for them to complete!')
    else:
        write_entries(database_file_path, all_files, docs_sources, max_version)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description='This program generates the database entries for the docset.')
    parser.add_argument('-s',
                        '--sources',
                        type=str,
                        help='The directory on disk where the formatted documentation is located.')
    parser.add_argument('-o',
                        '--output',
                        type=str,
                        help='The full path to where the database should be written to.')
    parser.add_argument('-mv',
                        '--maxVersion',
                        default='2017',
                        help='The 3ds max version to generate the docset for.')
    parser.add_argument('-mt',
                        '--multiThread',
                        default=False,
                        type=bool,
                        help='If set to True, will run jobs in parallel. Uses more system resources.')
    args = parser.parse_args()
    main(args.sources, args.output, args.maxVersion, args.multiThread)
