추가 키워드 검색 필요 열



추가 아이디어
앞뒤 문맥 짧은 구문 추출시 앞뒤가 Stopword라면 제외시키고 뽑도록 구성

📝 기존 Filter_Context 문자열
예시:
[FE's Issue Description] 'double' →...orner. If you start exam with **double** click it'll come with an empt...
이럴때 with는 stopword로되어 제외하고 double click만 뽑히도록하고 싶다

이때 사용될 stopwords는 hybrid_matcher.py의 stop_words를 사용 하나?
