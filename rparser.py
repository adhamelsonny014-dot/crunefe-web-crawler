import requests
from urllib.parse import urlparse
import re

def parse_robots(url):
    try:
        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Extract domain from URL if full URL provided
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Request robots.txt
        response = requests.get(f"{base_url}/robots.txt", timeout=10)
        response.raise_for_status()
        
        # Initialize data structure for rules
        rules = {
            "user_agents": {},
            "sitemaps": [],
            "host": None,
            "default": {"allow": [], "disallow": [], "delay": None}
        }
        
        # Default to no specific user agent
        current_agent = None
        
        # Parse the file
        for line in response.text.splitlines():
            # Remove comments
            if '#' in line:
                line = line.split('#', 1)[0]
                
            line = line.strip()
            if not line:
                continue
                
            # Extract directive and value
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
                
            directive = parts[0].strip().lower()
            value = parts[1].strip()
            
            if directive == "user-agent":
                current_agent = value.lower()
                
                # Handle default user agent (*)
                if current_agent == "*":
                    current_agent = "default"
                
                # Initialize user agent if needed
                if current_agent != "default" and current_agent not in rules["user_agents"]:
                    rules["user_agents"][current_agent] = {"allow": [], "disallow": [], "delay": None}
                    
            elif directive == "disallow" and value:  # Only process non-empty disallow rules
                if not current_agent or current_agent == "default":
                    rules["default"]["disallow"].append(value)
                else:
                    rules["user_agents"][current_agent]["disallow"].append(value)
                    
            elif directive == "allow" and value:  # Only process non-empty allow rules
                if not current_agent or current_agent == "default":
                    rules["default"]["allow"].append(value)
                else:
                    rules["user_agents"][current_agent]["allow"].append(value)
                    
            elif directive == "crawl-delay":
                try:
                    delay = float(value)
                    if not current_agent or current_agent == "default":
                        rules["default"]["delay"] = delay
                    else:
                        rules["user_agents"][current_agent]["delay"] = delay
                except ValueError:
                    pass
                    
            elif directive == "sitemap":
                rules["sitemaps"].append(value)
                
            elif directive == "host":
                rules["host"] = value
        
        # If robots.txt exists but has no rules, it's completely permissive
        if not rules["default"]["disallow"] and not rules["default"]["allow"] and not rules["sitemaps"] and not rules["user_agents"]:
            rules["empty"] = True
        else:
            rules["empty"] = False
                
        return rules
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        return {"error": f"Error parsing robots.txt: {str(e)}"}

def calculate_score(rules):
    if "error" in rules:
        return {"score": 0, "reason": "Error fetching or parsing robots.txt"}
    
    # Initialize score components
    score = 100
    penalties = 0
    bonuses = 0
    reasons = []
    
    # If robots.txt is empty or not found, it's fully permissive
    if rules.get("empty", False):
        return {"score": 100, "reason": "No restrictions found in robots.txt (fully permissive)"}
    
    # Check global directives
    if rules["default"]["disallow"]:
        if "/" in rules["default"]["disallow"]:
            penalties += 40  # Heavy penalty for blocking everything
            reasons.append("Heavy penalty (-40) for blocking everything for default user agent")
        else:
            penalty = len(rules["default"]["disallow"]) * 3
            penalties += penalty
            reasons.append(f"Penalty (-{penalty}) for {len(rules['default']['disallow'])} disallow rules for default user agent")
    
    if rules["default"]["delay"]:
        if rules["default"]["delay"] > 5:
            penalties += 30
            reasons.append(f"Heavy penalty (-30) for high crawl delay: {rules['default']['delay']}")
        elif rules["default"]["delay"] > 1:
            penalties += 15
            reasons.append(f"Medium penalty (-15) for moderate crawl delay: {rules['default']['delay']}")
        else:
            penalties += 5
            reasons.append(f"Small penalty (-5) for low crawl delay: {rules['default']['delay']}")
    
    # Check if common crawlers are blocked
    bot_penalties = 0
    for agent in ["googlebot", "bingbot", "yandexbot"]:
        if agent in rules["user_agents"]:
            agent_rules = rules["user_agents"][agent]
            if "/" in agent_rules.get("disallow", []):
                bot_penalties += 10
                reasons.append(f"Penalty (-10) for blocking {agent}")
    
    actual_bot_penalty = min(bot_penalties, 30)  # Cap bot penalties
    if bot_penalties > actual_bot_penalty:
        reasons.append(f"Bot penalties capped to {actual_bot_penalty} (from {bot_penalties})")
    penalties += actual_bot_penalty
    
    # Bonuses
    if rules["sitemaps"]:
        sitemap_bonus = min(len(rules["sitemaps"]) * 5, 15)  # Bonus for sitemaps
        bonuses += sitemap_bonus
        reasons.append(f"Bonus (+{sitemap_bonus}) for {len(rules['sitemaps'])} sitemaps")
    
    if rules["default"]["allow"]:
        allow_bonus = min(len(rules["default"]["allow"]) * 2, 10)
        bonuses += allow_bonus
        reasons.append(f"Bonus (+{allow_bonus}) for {len(rules['default']['allow'])} explicit allow rules")
    
    # Calculate final score
    final_score = 100 - penalties + bonuses
    final_score = max(min(final_score, 100), 0)  # Ensure score is between 0-100
    
    # Summary reason
    summary = f"Score: {final_score}/100 (Base 100 - {penalties} penalties + {bonuses} bonuses)"
    
    return {
        "score": final_score,
        "penalties": penalties,
        "bonuses": bonuses,
        "summary": summary,
        "reasons": reasons
    }

def analyze_robots(url):
    rules = parse_robots(url)
    score_data = calculate_score(rules)
    
    if isinstance(score_data, dict):
        score = score_data["score"]
        score_details = score_data
    else:
        score = score_data
        score_details = {"score": score}
    
    analysis = {
        "url": url,
        "score": score,
        "score_details": score_details,
        "rules": rules,
        "interpretation": ""
    }
    
    # Generate interpretation
    if score >= 90:
        analysis["interpretation"] = "Very crawler-friendly. This site welcomes search engines."
    elif score >= 70:
        analysis["interpretation"] = "Crawler-friendly with some restrictions."
    elif score >= 50:
        analysis["interpretation"] = "Moderately restrictive to crawlers."
    elif score >= 30:
        analysis["interpretation"] = "Significantly restrictive to search engines."
    else:
        analysis["interpretation"] = "Highly restrictive or blocking most crawlers."
        
    return analysis

def print_robots_analysis(url):
    """
    Analyze a robots.txt file and print detailed results
    """
    analysis = analyze_robots(url)
    
    print(f"\n====== Robots.txt Analysis for {url} ======")
    
    # Print the score and interpretation
    print(f"\nScore: {analysis['score']}/100")
    print(f"Interpretation: {analysis['interpretation']}")
    
    # Print score details if available
    if "score_details" in analysis and "reasons" in analysis["score_details"]:
        print("\nScore breakdown:")
        for reason in analysis["score_details"]["reasons"]:
            print(f"  - {reason}")
    
    # Print basic rule statistics
    rules = analysis["rules"]
    if "error" in rules:
        print(f"\nError: {rules['error']}")
        return
    
    print("\nSummary of rules:")
    print(f"  Sitemaps: {len(rules['sitemaps'])}")
    print(f"  User agents with specific rules: {len(rules['user_agents'])}")
    print(f"  Default disallow rules: {len(rules['default']['disallow'])}")
    print(f"  Default allow rules: {len(rules['default']['allow'])}")
    print(f"  Default crawl delay: {rules['default']['delay'] if rules['default']['delay'] else 'None'}")
    
    # Print more detailed information
    if rules["sitemaps"]:
        print("\nSitemaps:")
        for sitemap in rules["sitemaps"]:
            print(f"  - {sitemap}")
    
    # print("\nDefault rules:")
    # if rules["default"]["disallow"]:
    #     print("  Disallow:")
    #     for rule in rules["default"]["disallow"]:
    #         print(f"    - {rule}")
    # else:
    #     print("  No global disallow rules (fully permissive)")
        
    # if rules["default"]["allow"]:
    #     print("  Allow:")
    #     for rule in rules["default"]["allow"]:
    #         print(f"    - {rule}")
    
    # # Print rules for major bots
    # major_bots = ["googlebot", "bingbot", "yandexbot"]
    # found_bots = [bot for bot in major_bots if bot in rules["user_agents"]]
    
    # if found_bots:
    #     print("\nRules for major search engines:")
    #     for bot in found_bots:
    #         print(f"  {bot}:")
    #         bot_rules = rules["user_agents"][bot]
            
    #         if bot_rules["disallow"]:
    #             print("    Disallow:")
    #             for rule in bot_rules["disallow"]:
    #                 print(f"      - {rule}")
    #         else:
    #             print("    No disallow rules")
                
    #         if bot_rules["allow"]:
    #             print("    Allow:")
    #             for rule in bot_rules["allow"]:
    #                 print(f"      - {rule}")
            
    #         if bot_rules["delay"]:
    #             print(f"    Crawl delay: {bot_rules['delay']}")
    
    print("\n================================================\n")


# if __name__ == "__main__":
#     # Test with a few different websites
#     test_sites = [
#         "https://www.reuters.com",
#         "https://www.amazon.com",
#         "https://www.google.com",
#         "https://www.instagram.com"
#     ]
    
#     for site in test_sites:
#         print_robots_analysis(site)