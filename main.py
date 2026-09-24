from extractor import mainy 
import os
from rparser import print_robots_analysis, analyze_robots
from jsAPInew import maino, maina
import asyncio
import json
import subprocess

# def analyze_site(url):
#     print(f"\nAnalyzing: {url}")

#     # robots.txt
#     rules = parse_robots_txt(url)
#     if rules:
#         #rules = parse_robots_txt(robots_txt)
#         score = calculate_score(rules)
#         print(f"Crawlability Score: {score}/100")
#     else:
#         print("No robots.txt found. Assuming default crawlability.")

#     # JS/API/RSS check
#     print("Checking RSS feeds...")
#     rss = check_rss(url)
#     print(f"RSS feeds found: {rss or 'None'}")

#     print("Checking open API...")
#     api = check_open_api(url)
#     print(f"Open API found at: {api or 'None'}")

if __name__ == "__main__":
    
   crawler = """
    ██████   ██████   ██     ██  ███    ██  ██████  ██████  ██████ 
    ██       ██   ██  ██     ██  ████   ██  ██      ██      ██     
    ██       ██████   ██     ██  ██ ██  ██  █████   █████   █████  
    ██       ██   ██  ██     ██  ██  ██ ██  ██      ██      ██     
    ██████   ██   ██   ███████   ██   ████  ██████  ██      ██████ 
        
        WEB CRAWLER BY ADHAM, LOJAIN, OMAR
        """

   
    
   menu = """
    Please choose an option:

    1. Analyze site
    2. Extract Data
    3. Open Dashboard
    4. Exit
    """
   flag = False
   while True:
        os.system('cls')
        print(crawler)
        print(menu)
        link = "https://www.reuters.com"
        link2 = "https://www.reuters.com"
        porsche = "https://www.instagram.com"
        baba = "https://www.nytimes.com"
        
        
        choice = input("Enter your choice: ")

        if choice == "1":
            os.system('cls')
            uni = input("Enter you website address: ")
            print("🟢 Starting the analyzer...")
            print_robots_analysis(uni)
            
            s = analyze_robots(uni)
            score = s['score']
            
            with open("crawlability_score.json", "w") as f:
                json.dump({"score": score}, f)
            
            print("\n " * 3,"######JAVA-SCRIPT CHECKER ######" ,"______________________________")
            
            asyncio.run(maina(uni))
            input("\n Press Enter when you're done reading")
            flag = True
            
        elif choice == "2":
            os.system('cls')
            uni = input("Enter you website address")
            if flag == True:
                print("📄 Loading extractor...")
                mainy()
                input("\n Press Enter when you're done reading")
            else:
                print("\n We recommend you to analyze the link first to check the coed of crawlability :) ")
                ch = input("\n Do you wish to proceed (y/n): ")
                if ch == 'y':
                    print("📄 Loading extractor...")
                    mainy(uni)
                    input("\n Press ANY KEY when you're done reading")
                
                
        
        elif choice == "3":
            print("⚙️ Opening Dashboard..")
            dashboard_path = "E:/College Work 3rd year/Semester 2/Information Retrieval/Project/final project IR/dashbo.py"  # replace if your dashboard file has a different name
            subprocess.run(["python", "-m", "streamlit" ,"run", dashboard_path])
            input("\n Press Enter when you're done reading")
            
            
        elif choice == "4":
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice. Please try again.")
