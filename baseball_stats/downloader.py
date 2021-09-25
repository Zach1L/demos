import concurrent.futures
import logging 

def parallel_downloads(url_parse_fcn, urls):
    """
    Download / Sanatize Data in Parallel 
    """
    pitching_df_list = []
    batting_df_list= []
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(url_parse_fcn, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                _dict = future.result()
                if 'p' in _dict.keys():
                    pitching_df_list.append(_dict['p'])
                if 'b' in _dict.keys():
                    batting_df_list.append(_dict['b'])
            except Exception as exc:
                logging.warn('%r generated an exception: %s' % (url, exc))
            else:
                logging.debug(f'delogged dict {url}')
    return pitching_df_list, batting_df_list