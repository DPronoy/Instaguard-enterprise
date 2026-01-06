from playwright.sync_api import sync_playwright, Error
import time
import os
import json

class EnterpriseScraper:
    def __init__(self):
        self.base_dir = os.getcwd()
        self.evidence_dir = os.path.join(self.base_dir, "evidence")
        if not os.path.exists(self.evidence_dir): os.makedirs(self.evidence_dir)

    def load_cookies(self, context):
        """Injects cookies from cookies.json if available"""
        cookie_file = "cookies.json"
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                    # Playwright needs 'sameSite' to be strictly defined or lowercase
                    for c in cookies:
                        if 'sameSite' in c and c['sameSite'] not in ["Strict", "Lax", "None"]:
                            c['sameSite'] = "None"
                    context.add_cookies(cookies)
                print("🍪 Session Cookies Injected Successfully.")
                return True
            except Exception as e:
                print(f"⚠️ Cookie Injection Failed: {e}")
                return False
        else:
            print("⚠️ No 'cookies.json' found. You will hit the Login Wall.")
            return False

    def clean_text(self, text):
        t = text.strip()
        if len(t) < 2: return None
        garbage = ["Reply", "See translation", "View all", "Log in", "Sign up", "Liked by", "View more comments", "d", "h", "m"]
        if any(g == t for g in garbage): return None 
        if any(g in t for g in ["function()", "var ", "{", "}"]): return None
        return t

    def run(self, url, max_limit, analyzer):
        findings = []
        count = 0
        seen_comments = set()
        
        with sync_playwright() as p:
            print(" Launching Authenticated Session...")
            
            iphone = p.devices['iPhone 13 Pro']
            # Clean keys to prevent crash
            keys_to_remove = ['default_browser_type', 'defaultBrowserType']
            for k in keys_to_remove:
                if k in iphone: del iphone[k]
            
            # Launch standard browser first (NOT persistent context yet)
            browser = p.chromium.launch(
                headless=False,
                channel="msedge", # or "chrome"
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            # Create a Context (This is where we inject mobile settings)
            context = browser.new_context(**iphone)
            
            # --- CRITICAL: INJECT COOKIES HERE ---
            self.load_cookies(context)
            
            page = context.new_page()
            
            try:
                print(f" Opening Post: {url}")
                page.goto(url, timeout=60000)
                
                # Check if injection worked
                try:
                    # If we see the "Log In" button, injection failed or cookies expired
                    if page.locator("text='Log in'").count() > 0:
                        print("Cookie Authentication Failed. Login screen detected.")
                        print("ACTION: Update your 'cookies.json' file.")
                except: pass

                print("Scanning Comments...")
                time.sleep(3)

                stuck_counter = 0
                last_count = 0

                while count < max_limit:
                    if page.is_closed(): break

                    # Swipe
                    try:
                        page.mouse.move(190, 600)  
                        page.mouse.down()
                        page.mouse.move(190, 100, steps=10) 
                        page.mouse.up()
                    except: break
                    
                    time.sleep(1.5)

                    # Scan
                    try:
                        comment_elements = page.locator("ul > li, div[role='button']").all()
                    except: break

                    # Load More
                    if len(comment_elements) == last_count:
                        stuck_counter += 1
                        if stuck_counter > 3:
                            try:
                                if not page.is_closed():
                                    page.locator("circle").first.click(timeout=1000)
                                    print("Loading more...")
                                    stuck_counter = 0
                            except:
                                if stuck_counter > 6: break
                    else:
                        stuck_counter = 0
                    last_count = len(comment_elements)

                    # Process
                    batch = comment_elements[-20:] if len(comment_elements) > 20 else comment_elements
                    for el in batch:
                        if count >= max_limit: break
                        try:
                            if page.is_closed(): break
                            
                            raw_text = el.inner_text().replace("\n", " ")
                            text = self.clean_text(raw_text)
                            
                            if not text: continue
                            if len(text.split()) == 1 and len(text) < 15: continue 
                            
                            if text in seen_comments: continue
                            seen_comments.add(text)

                            res = analyzer.scan(text)
                            
                            if res['is_toxic']:
                                print(f"MATCH: {text[:30]}... [{res['reason']}]")
                                
                                el.scroll_into_view_if_needed()
                                time.sleep(0.5)
                                
                                el.evaluate("node => { node.style.border = '3px solid red'; node.style.backgroundColor = 'rgba(255,0,0,0.1)'; }")
                                img_path = os.path.join(self.evidence_dir, f"evidence_{count}.png")
                                page.screenshot(path=img_path)
                                el.evaluate("node => { node.style.border = ''; node.style.backgroundColor = ''; }")

                                findings.append({
                                    "text": text,
                                    "reason": res['reason'],
                                    "link": url,
                                    "image": img_path
                                })
                                count += 1
                        except: continue

            except Exception as e:
                print(f"Error: {e}")
            
            finally:
                try: browser.close()
                except: pass
                
            return findings