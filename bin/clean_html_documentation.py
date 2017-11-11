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


def format_files(all_files, docs_path, output_path, job_number=0):
    """
    This function formats the ``list`` of HTML documentation files given and
    writes the output files to a subdirectory.
    """
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('format_files_{0}'.format(str(job_number)))
    for i, f in enumerate(all_files):
        if os.path.splitext(f)[-1] != '.html':
            continue
        logger.debug('Processing: {0}...'.format(f))
        html = open(os.path.join(docs_path, f)).read()
        soup = BeautifulSoup(html, 'html.parser')

        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                img['src'] = src.replace('cpp_ref/', './')

        for script in soup.find_all('script'):
            src = script.get('src')
            if src:
                if 'www.microsofttranslator.com' in src:
                    script['src'] = ''
                elif 'adsk.redirect.js' in src:
                    # NOTE (regionstormer): remove redirect - or we get blank pages/index page all the time
                    script['src'] = ''
                else:
                    script['src'] = src.replace('../scripts', './scripts')

        links = soup.find_all('a') + soup.find_all('link')

        for link in links:
            href = link.get('href')
            if href:
                link['href'] = href.replace('style/', './')\
                                   .replace('#!/url=./cpp_ref/', './')\
                                   .replace('cpp_ref/', './')

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
    """
    This is the main entry point of the program. It formats the HTML sources
    specified in ``docs_sources`` and writes them to the ``output_path`` directory
    specified.

    :param docs_sources: ``str`` path to the original documentation sources. This
        should contain the ``cpp_ref`` folder, among other resources.

    :param output_path: ``str`` path to write the formatted HTML files to.

    :param multi_thread: ``bool`` to indicate if multithreading support should be
        enabled.

    :param max_version: ``str`` indicating what version of 3ds max the docset
        being generated for is.
    """
    logger = logging.getLogger(__name__)
    if not docs_sources:
        docs_sources = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    'resources',
                                    max_version,
                                    'cpp_ref')
    if not output_path:
        output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'max-{0}-cpp.docset'.format(max_version),
                                'Contents',
                                'Resources',
                                'Documents')
    if docs_sources == output_path:
        raise IOError('The source and output directories are the same!')
    if not os.path.isdir(docs_sources):
        raise IOError('The directory: {0} does not exist!'.format(docs_sources))

    logger.info('Formatting documentation...')

    if os.path.isdir(output_path):
        logger.debug('Removing existing directory: {0}!'.format(output_path))
        shutil.rmtree(output_path)
    os.makedirs(output_path)

    # NOTE (sonictk): Copy over the necessary resource files first
    styles_path = os.path.join(os.path.dirname(docs_sources), 'style')
    if not os.path.isdir(styles_path):
        raise IOError('The CSS styles directory: {0} does not exist!'.format(styles_path))
    [shutil.copy(os.path.join(styles_path, css), output_path) for css in os.listdir(styles_path)]

    scripts_path = os.path.join(os.path.dirname(docs_sources), 'scripts')
    if not os.path.isdir(scripts_path):
        raise IOError('The JScript directory: {0} does not exist!'.format(scripts_path))
    shutil.copytree(scripts_path, os.path.join(output_path, 'scripts'))

    all_files = os.listdir(docs_sources)
    logger.debug('Total number of files to process: {0}'.format(len(all_files)))
    for f in all_files:
        if os.path.splitext(f)[-1] != '.html':
            # NOTE (sonictk): Just copy it over anyway, since those files are needed (CSS, scripts etc.)
            shutil.copy(os.path.join(docs_sources, f), output_path)
    if multi_thread:
        jobs = []
        for idx, s in enumerate(chunk(all_files, 500)):
            job = multiprocessing.Process(target=format_files, args=(s, docs_sources, output_path, idx))
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
                        default='2017')
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
