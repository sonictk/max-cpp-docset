#!/usr/bin/env python
"""
This module is a script that cleans up the default HTML 3ds max Doxygen
documentation to be usable as standalone.
"""
import argparse
import logging
import multiprocessing
import os
import shutil
from bs4 import BeautifulSoup
from lib import chunk


def format_files(all_files, docs_path, output_path):
    """
    This function formats the ``list`` of HTML documentation files given and
    writes the output files to a subdirectory.
    """
    logger = logging.getLogger(__name__)
    # NOTE (sonictk): Copy over the necessary resource files first

    for i, f in enumerate(all_files):
        if os.path.splitext(f)[-1] != '.html':
            continue

        html = open(os.path.join(docs_path, f)).read()
        soup = BeautifulSoup(html, 'html.parser')
        
        for script in soup.find_all('script'):
            src = script.get('src')
            if src and 'www.microsofttranslator.com' in src:
                script['src'] = ''
        
        links = soup.find_all('a') + soup.find_all('link')

        for link in links:
            href = link.get('href')
            if href: 
                if '#!/url=./cpp_ref/' in href:
                    new_href = href.replace('#!/url=./cpp_ref/', './')
                elif 'cpp_ref/' in href:
                    new_href = href.replace('cpp_ref/', './')
                else:
                    continue
                link['href'] = new_href

        # Also insert anchors in order for table of contents to work
        for td in soup.find_all('td'):
            if td.get('class') and 'memname' in td.get('class') and td.a:
                member_name = td.contents[-1]
                if member_name and len(member_name) > 2:
                    member_name_components = member_name.split(' ')
                    if len(member_name_components) < 2:
                        logger.warning('Skipped member: {0}!'.format(member_name))
                        continue
                    member_name = member_name_components[-2]
                    new_tag = soup.new_tag('a')
                    new_tag['name'] = '//apple_ref/cpp/Function/{0}'.format(member_name)
                    new_tag['class'] = 'dashAnchor'
                    td.insert(0, new_tag)

        with open(os.path.join(output_path, f), 'w') as of:
            of.write(str(soup))

    logger.debug('Job complete!')


def main(docs_sources, output_path, multi_thread=False, max_version='2017'):
    """This is the main entry point of the program."""

    logger = logging.getLogger(__name__)
    if not docs_sources:
        sources_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                    'resources',
                                    max_version,
                                    'cpp_ref')
    if not output_path:
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                'max-{0}-cpp.docset',format(max_version),
                                'Contents',
                                'Resources',
                                'Documents')
    if docs_sources == output_path:
        raise IOError('The source and output directories are the same!')
    if not os.path.isdir(docs_sources):
        raise IOError('The directory: {0} does not exist!'.format(docs_sources))

    logger.info('Formatting documentation...')

    if os.path.isdir(output_path):
        logger.debug('Removing existing directory: {0}...'.format(output_path))
        shutil.rmtree(output_path)
    os.makedirs(output_path)

    all_files = os.listdir(docs_sources)
    logger.debug('Total number of files to process: {0}'.format(len(all_files)))
    jobs = []
    if multi_thread:
        for s in chunk(all_files, 500):
            job = multiprocessing.Process(target=format_files, args=(s, docs_sources, output_path))
            jobs.append(job)
        logger.debug('Num. of jobs scheduled: {0}'.format(len(jobs)))
        [j.start() for j in jobs]
        logger.info('Jobs submitted, please wait for them to complete!')
    else:
        format_files(all_files, docs_sources, output_path)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description='This program formats the HTML documentation so that it is usable in the docset.')
    parser.add_argument('-s',
                        '--sources',
                        type=str,
                        help='The directory on disk where the original documentation is located.')
    parser.add_argument('-o',
                        '--output',
                        type=str,
                        help='The directory on disk where the newly-formatted documentation should be written to.')
    parser.add_argument('-mv',
                        '--maxVersion',
                        type=str,
                        help='The 3ds max version of the docset to generate.',
                        required=True)
    parser.add_argument('-mt',
                        '--multiThread',
                        default=False,
                        type=bool,
                        help='If set to True, will run jobs in parallel. Uses more system resources.')
    cmdline_args = parser.parse_args()
    main(cmdline_args.sources,
         cmdline_args.output,
         cmdline_args.multiThread,
         cmdline_args.maxVersion)
