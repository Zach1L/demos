## Overview
### This code:  
1. Scrapes basic pitching and batting data from the MLB for all active player from [Baseball Reference](https://www.baseball-reference.com/)  
2. Perfoms a modfied [TOPSIS](https://en.wikipedia.org/wiki/TOPSIS) algorithm to determine the most effective player across a set of catagories

### Running
1. Set up a virtual environment and install the `requirements.txt` file
2. In the virtual environment run `.\baseball_stats\run_me.py`
3. It will take some time to download all data
4. After the script has finished open `.\batter_rankings.csv` in the run directory:
    1. Shows the batters ranked in order for a currently hardcoded set of metrics 