# youtube-scraper
youtube-scraper - scraper app which is able to scrap video title, video link, views, comments, thumbnail from youtube
[https://youtube-scraper-1.herokuapp.com]

* git clone git@github.com:ritesh-tiwary/youtube-scraper.git
* git remote -v
* git pull origin master --allow-unrelated-histories
* git add .
* git commit -m "Initial commit"
* git status
* git log
* git push -u origin main

---

* heroku logs --tail -a youtube-scraper-1
* heroku addons:create heroku-postgresql:hobby-dev -a youtube-scraper-1
* heroku pg:info -a youtube-scraper-1
* heroku pg:credentials:url -a youtube-scraper-1 

---

- Created postgresql-rectangular-93245 as DATABASE_URL
- Use heroku addons:docs heroku-postgresql to view documentation

