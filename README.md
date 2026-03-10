# FashionWeek_StockImpact
This project aims to quantify the influence of Fashion Weeks on public brand perception and, indirectly, on the stock market performance of luxury brands. It uses Google Trends search data as an indicator of consumer interest and engagement and Yahoo Finance for the financial data.

Scope: 

We are going to focus on the "Big 4" Fashion Weeks : Paris, Milan, London, New York and for each, a selection of their top brands with publicly traded stock data : 
  - Paris : Christian Dior, Louis Vuitton, Hermes
    Dior and Louis Vuitton belong to the same group LVMH, therefore theire data will be joined
  - Milan : Prada, Gucci
    Same with Gucci who belongs to Kering as well as Saint Laurent, Bottega Veneta, ...
  - London : Burberry
  - New York : Ralph Lauren, Tommy Hilfiger, Calvin Klein
    Tommy and Calvin belong to the group PVH

Brand like Chanel and Vivienne Westwood are excluded from this project because as private companies they do not have stock market tickers.

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
| Brand           | Fashion Week | yfinance Ticker | Market         |                              
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
| Dior            | Paris        | MC.PA         | Euronext Paris |
| Louis Vuitton   | Paris        | MC.PA         | Euronext Paris |
| Hermes          | Paris        | RMS.PA          | Euronext Paris |
| Prada           | Milan        | 1913.HK         | Hong Kong      |
| Gucci           | Milan        | KER.PA          | Euronext Paris |
| Burberry        | London       | BRBY.L          | London         |
| Ralph Lauren    | New York     | RL              | NYSE           |
| Tommy Hilfiger  | New York     | PVH             | NYSE           |
| Calvin Klein    | New York     | PVH             | NYSE           |
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Data Collecting:

The Consumer Interest Data is collected from Google Trends API via the pytrends Pyhton library. The analysis will focus on worldwide search interest.

The financial data is historical stock data collected from Yahoo Finance API using the yfinance Python library, Yahoo Finance API Wrapper.

Future developments:
Using NLP methods to add social medias impressions for calculating the brand impact with Instagram API (Meta Graph API) or X API (Tweepy library)
- NLP sentiment analysis : integrating social media data (eg: from X or Meta API) to perform sentiment analysis
- Buzz and virality metrics : using NLP and social media data to quantify the "buzz" and virality of specific show or items to see if it correlates with search interest.

Limits:

Google Trends Data Shift : On the 01/01/22, Google Trends implemented a significant change to its data collecting system, meaning that data from before this date is not directly comparable to data after it. 

Conglomerate "smoothing" : Brands belonging to large holdings like LVMH or Kering have their individal impact "smoothed" bu the overall performance of the group's portfolio. For example : a spike in interest for Gucci may not significantly move the KER.PA stock if other group brands are underperforming. On the other hand, for brands such as Ralph Lauren, with its own stock index, we could clearly detect the impact (or no) of NYFW.

