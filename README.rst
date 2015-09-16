Documentation
=============

EARN is a national nonprofit that gives working families the power to create prosperity for generations.
As the nation’s leading microsavings provider, EARN gives families the tools to achieve life-changing goals such as saving for college,
buying a first home, or starting a small business. EARN's ultimate vision is that millions of well-informed,
working American families will achieve financial success through proven strategies, fair public policy, and their own hard work.

This  is a REST based Web Service that is used by EARN.org Web applications to look up the income levels
of applicants to determine their  eligibility  for our matched savings programs.

https://www.earn.org/for-savers/our-programs/

The Income Limits  data Web pages

FY2015
http://www.huduser.org/portal/datasets/il/il15/index.html
FY2014
http://www.huduser.org/portal/datasets/il/il14/index.html

Median Income

Sample url:                     http://lmi.earn.org:6543/v1/county/Chicago/IL/60645/median/l50_3
Sample result:                "{\"city\": \"Chicago\", \"state\": \"IL\", \"zipcode\": \"60645\", \"fips\": \"1703199999\", \"median_income\": 72400, \"l50_3\": 32600}"

So build another sample url by substituting a city name/state abbreviation/zip code
Income Eligibility Test - true/false

Sample url:                     http://lmi.earn.org:6543/v1/county/Chicago/IL/60645/median/l50_3/23000
Sample result:                "{\"city\": \"Chicago\", \"state\": \"IL\", \"zipcode\": \"60645\", \"fips\": \"1703199999\", \"median_income\": 72400, \"l50_3\": 32600, \"income\": 23000, \"eligibility\": true}"
The 23000 reported income is under the 32,600 adjusted household income for 3.
So build another sample by changing the city name, state, zip code, median, l50=level50% and household size 3>, income amount from 1040 = 23000, true meaning they quality for program.

So if Elon Musk applied for the program:
Sample url:  http://lmi.earn.org:6543/v1/county/san%20francisco/ca/94104/median/l50_2/4000000
Sample results: "{\"city\": \"San Francisco\", \"state\": \"CA\", \"zipcode\": \"94104\", \"fips\": \"0607599999\", \"median_income\": 97100, \"l50_2\": 44300, \"income\": 2000000, \"eligibility\": false}"
Conclusion: a household of 2 in SF, has an adjusted income of 44300 max, while the reported income is 2,000,000, he will not qualify for program.






