import logging,requests,time,csv, sys
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from requests_html import HTMLSession


# Get the values  from the command line arguments
# site = sys.argv[1]
# max_courses = sys.argv[2]
# max_days_old = sys.argv[3]
# # Create CSV file and write header row
with open('courses.csv', 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Course Name', 'Course URL', 'Coupon Code', 'Expiration Date'])

def scrap_page_request_html(url: str):
    session = HTMLSession()
    request = session.get(url)
    return request.content

def screen_message(msg: str):
    with open('scrap_output.txt', 'a', newline='') as f:
        f.write(str(datetime.utcnow()) + " | " + msg +'\n')

def scrap_page(url: str, clicks: int = 1):
    driver = webdriver.Chrome()
    driver.get(url)
    if url == 'https://www.real.discount/udemy-coupon-code/':
        button = driver.find_element(by='css selector', value="input.btn.btn-primary[onclick='load_all(2)']")

        for _ in range(clicks):
            button.click()
            time.sleep(1)
    time.sleep(5)
    return driver.page_source

def check_udemy(url: str):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(5)
    udemy_data = filter_scrap(driver.page_source).findAll('div', class_='price-text--price-part--2npPm ud-clp-discount-price ud-heading-xxl')[0].find_all('span')[1].text
    # udemy_data = filter_scrap(scrap_page_request(url)).findAll('div', class_='price-text--price-part--2npPm ud-clp-discount-price ud-heading-xxl')[0].find_all('span')[1].text
    return udemy_data

def scrap_page_request(url: str):
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
    return requests.get(url=url, headers=headers).content

def filter_scrap(content):
    return BeautifulSoup(content, 'html.parser')

def web_scrap(url: str, max_courses: int, max_days_old: int ):
    if url == 'https://www.real.discount':
        base_url = url
        per_page = 10
        count = 1
        filtered_courses = []

        clicks_input = int((max_courses / per_page) + 3)
        current_time = datetime.utcnow()

        screen_message(f"Scrapping the Website {base_url}")
        first_data = filter_scrap(scrap_page(base_url + "/udemy-coupon-code/",clicks_input))
        #Find all courses on the page
        courses_content = first_data.findAll('ul', class_='list-unstyled', id='myList' )

        for course in courses_content:
            for li in course.find_all('li'):
                if count <= max_courses:
                    course_name = li.find('h3', {'class': 'ml-3'}).text.strip()
                    course_link = li.find('a')["href"].strip()  
                    if course_link.startswith("/offer"):
                        screen_message(f"Found course {course_name}")
                        course_url = base_url + course_link
                        second_data = filter_scrap(scrap_page_request(course_url))
                        coupon_content = second_data.findAll('div', class_='mt-4')[3].find_all('a')[0]['href']
                        if coupon_content.startswith("https://www.udemy.com/course"):
                            #checking the date the course was uploaded and ensures it not older than the max days set
                            screen_message(f"Checking if the course {course_name} is not older than {max_days_old} days")
                            update_date = second_data.findAll('div', class_='card-body')[0].find_all('span', class_="flask-moment")[0]['data-timestamp']
                            update_date = datetime.fromisoformat(update_date[:-1])
                            days_elapsed = (current_time - update_date).days
                            
                            if days_elapsed <= max_days_old:
                                #checking if the course is still free on udemy
                                screen_message(f"Checking if the course {course_name} is still free on Udemy")
                                is_free = check_udemy(coupon_content)
                                if is_free == "Free":
                                    screen_message(f"The course {course_name} is still free on Udemy")

                                    course_data = coupon_content.split("?")
                                    course_udemy_link = course_data[0]
                                    course_udemy_coupon = course_data[1].split("=")[1]

                                    expiry_date = second_data.findAll('div', class_='card-body')[0].find_all('span', class_="flask-moment")[1]['data-timestamp']
                                    expiry_date = datetime.fromisoformat(expiry_date[:-1])

                                    filtered_courses = [course_name, course_udemy_link, course_udemy_coupon, expiry_date]

                                    # Write filtered courses to CSV file
                                    with open('courses.csv', 'a',encoding='utf-8', newline='') as csvfile:
                                        writer = csv.writer(csvfile)
                                        writer.writerow(filtered_courses)
                                        screen_message(f'Added {course_name} courses to CSV file.')
                                    
                                    count += 1
                            else:
                                screen_message(f"the course {course_name} is no longer free, the coupon has expired !")
    
    elif url == 'https://www.couponscorpion.com':
        base_url = url
        per_page = 12
        count = 1
        filtered_courses = []

        clicks_input = int((max_courses / per_page) + 3)
        current_time = datetime.utcnow()
        
        screen_message(f"Scrapping the Website {base_url}")
        for click in range(clicks_input):
            click += 1
            web_data = filter_scrap(scrap_page_request_html(base_url + "/page/" + str(click)))

            courses_content = web_data.findAll('figure', class_="mb15")
            
            for course in courses_content:
                course_link = course.find('a')['href'].strip()
                course_name = course.find('img')['alt']
                screen_message(f"Found the course {course_name} on {base_url}")
                second_data = filter_scrap(scrap_page(course_link))
                update_date = second_data.find('span', class_='date_meta').text
                update_date = datetime.strptime(update_date, '%B %d, %Y')
                days_elapsed = (current_time - update_date).days
                            
                if days_elapsed <= max_days_old:
                    coupon_data = second_data.findAll('span', class_="rh_button_wrapper")[0].find_all('a')[0]['href'].split()[0]
                    udemy_link = scrap_page_request_html(coupon_data).url
                    screen_message(f"Checking if the course {course_name} is still free on Udemy")
                    is_free, expiry_day = check_udemy(udemy_link)
                    if is_free == "Free":
                        screen_message(f"The course {course_name} is still free on Udemy")
                        course_data = udemy_link.split("?")
                        course_udemy_link = course_data[0]
                        course_udemy_coupon = course_data[1].split("=")[1]
                        expiry = int(expiry_day.split(' ')[0])
                        expiry_date = current_time + timedelta(days=expiry)

                        filtered_courses = [course_name, course_udemy_link, course_udemy_coupon, expiry_date]
                        # Write filtered courses to CSV file
                        with open('courses.csv', 'a',encoding='utf-8', newline='') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(filtered_courses)
                            screen_message(f'Added {course_name} courses to CSV file.')
                    else:
                        screen_message(f"the course {course_name} is no longer free, the coupon has expired !")

    return screen_message(f"Done scraping site {url}")


def test(name):
    url = 'https://www.real.discount/udemy-coupon-code/'

    print(name)
    return scrap_page_request(url)

#web_scrap(site, max_courses, max_days_old)