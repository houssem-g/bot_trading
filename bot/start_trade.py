
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


# executor_url = driver.command_executor._url
# session_id = driver.session_id

def attach_to_session(executor_url, session_id):
    original_execute = WebDriver.execute
    def new_command_execute(self, command, params=None):
        if command == "newSession":
            # Mock the response
            return {'success': 0, 'value': None, 'sessionId': session_id}
        else:
            return original_execute(self, command, params)
    # Patch the function before creating the driver object
    WebDriver.execute = new_command_execute
    driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
    driver.session_id = session_id
    # Replace the patched function with original function
    WebDriver.execute = original_execute
    return driver

driver = webdriver.Chrome('E:/users\houssem/trading_analysis/bot/chromedriver.exe')
# url = driver.command_executor._url     
# session_id = driver.session_id           
# driver = webdriver.Remote(command_executor=url,desired_capabilities={})
# driver.close()   # this prevents the dummy browser
# driver.session_id = session_id
# print(url)
# print(session_id)
driver.get("https://iqoption.com/traderoom")
driver.maximize_window()
# bro = attach_to_session(url, session_id)
bro = attach_to_session("http://127.0.0.1:62337", "e94f47f72b7bccf51b8e63817c47b700")
# bro.get("http://www.wikipedia.fr")
# print(driver.find_element(By.XPATH, '').text)
action = webdriver.ActionChains(driver)
# element = driver.find_element_by_xpath('//*[@id="main-container"]/div[3]/header/div/nav/ul/li[2]/a') # or your another selector here
ActionChains(driver).move_by_offset(300, 50).click().perform() # Left mouse click, 200 is the x coordinate, 100 is the y coordinate
# ActionChains(driver).move_by_offset(200, 100).context_click().perform()