# maple-inven-crawler
[maplestory inven](http://www.inven.co.kr/board/maple/2299?my=chuchu&amp;sort=PID) crawler to analyze the trend of public opinion due to MapleStory probability manipulation incident

<br><br>

<p align="center">
  <img alt="Visualized Using Kibana " src="https://raw.githubusercontent.com/Kyurenpoto/maple-inven-crawler/main/kibana.png">
</p>

## Dependencies

### Python modules

* BeautifulSoup4
* selenium
* elasticsearch

### Others

* chrome
* chromedriver
* [docker-elk-kor](https://github.com/ksundong/docker-elk-kor)

## How to use

1. Install all dependencies
  - The chromedriver executable should be in the same directory as crawler.py 
2. Execute docker-elk-kor using docker-compose
3. Execute crawler

```
pythron crawler.poy [ip address of the host running docker-elk-kor]
```

> The crawler collects posts from 2021/02/18 KST, the beginning of the [MapleStory probability manipulation incident](https://namu.wiki/w/%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC%20%ED%99%95%EB%A5%A0%EC%A1%B0%EC%9E%91%20%EC%82%AC%EA%B1%B4/%EC%A0%84%EA%B0%9C), to the latest.
