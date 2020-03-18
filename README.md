# instagram_crawling


### 인스타그램 해시태그 크롤링 

#### 소스코드 : instagram_crawling_final.ipynb

- 데이터 수집 동기 
    - sns를 통해 어떤 제품이나 서비스의 트렌드 파악
    - 회사의 제품 인지도 파악
    
    
    
- 데이터 수집의 계획 및 주기 작성
    - instagram 로그인 -> 검색어 입력 -> 게시물 갯수가 가장 많은 검색결과 클릭 -> 최근게시물부터 게시물 내용 중 해시태그만 크롤링
    
    - selenium과 scrapy의 TextResponse 함수 사용
        - selenium : 키워드 검색, 게시물 로딩, 스크롤내리기 
        - scrapy의 TextResponse  : 로딩된 게시물들의 url 가져오기
        
    - TextResponse를 통해 받아온 각 url들의 html head 엘리먼트에서 해시태그들만 뽑아온다
    
    - instagram 웹페이지의 게시물 렌더링 특징
        - 최근게시물 기준으로, 맨 처음 24개의 게시물 렌더링
        - 한번스크롤을 끝까지 내리면 추가로 12개의 게시물 렌더링
        - 세번째 이후부터는 스크롤을 끝까지 내릴때 마다 추가로 9개의 게시물을 불러온다
        - 최근게시물의 전체 게시물 갯수는 항상 45개를 유지한다
        - 새로운 9개의 게시물이 렌더링되면 가장 앞서 화면에 렌더링된 게시물 9개에 해당하는 element가 사라진다
        
        
    
- 크롤링 함수 구성
    - class 내부의 함수들 : 로그인함수, 검색어/검색결과 클릭함수, 클롤링함수, element 렌더링 여부 확인함수
    - 크롤링 수행하는 함수들 
        - initial_crawling() : 최초 1번만 호출
        - second_crawling() : 최초 1번만 호출
        - repeat_crawling() : 반복 호출
    - crawling_start 함수 : class를 인스턴스화 시켜서 크롤링을 수행하고, 데이터프레임을 리턴한다
    
    

- 크롤링 시작 :
```python
from insta_crawling import crawling_start 

crawling_start( 검색키워드, 마지막 크롤링함수의 반복 횟수, mongdb에의 저장여부 )
```


    
- 데이터의 저장
    - AWS 서버의 mongodb 데이터 베이스에 크롤링 한 데이터를 저장
    - 데이터베이스에 저장할거면, crawling_start() 함수의 세번째 인자로 1 넘겨주기
    
    
    
- 프로젝트 회고
    - 크롤링 함수들 3개를 하나로 통합하기
    - 발생가능한 에러 예상하기
        - ex) 처음 인스타그램 웹페이지에 들어갔을때, 다른종류의 알림창이 뜨는 경우 대처법
        
    - scrapy로 크롤링 해보기
    - scrapy를 사용할때, selenium의 webdriver만 사용해서 크롤링 한다면 scrapy의 비동기적 작동이 문제없이 돌아갈 것인가?
    
    
    
    