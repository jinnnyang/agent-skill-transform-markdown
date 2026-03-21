import json
import urllib.request
import urllib.error
import os
import time
import sys
import socket

class OpenAI:
    """
    A simple OpenAI API client using only Python built-in libraries.
    Designed to mimic the basic usage of the official openai package.
    """
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if not self.api_key:
            raise ValueError("API key must be provided or set in OPENAI_API_KEY environment variable")
            
        self.chat = self.Chat(self)
        self.interrupt_count = 0
        
    class Chat:
        def __init__(self, client):
            self.client = client
            self.completions = self.Completions(client)
            
        class Completions:
            def __init__(self, client):
                self.client = client
                
            def create(self, model, messages, retries=3, request_timeout=60, **kwargs):
                url = f"{self.client.base_url.rstrip('/')}/chat/completions"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.client.api_key}"
                }
                
                data = {
                    "model": model,
                    "messages": messages,
                    **kwargs
                }
                
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method='POST'
                )
                
                last_exception = None
                for attempt in range(retries):
                    try:
                        with urllib.request.urlopen(req, timeout=request_timeout) as response:
                            result = json.loads(response.read().decode('utf-8'))
                            self.client.interrupt_count = 0  # Reset on success
                            return self._parse_response(result)
                            
                    except KeyboardInterrupt:
                        self.client.interrupt_count += 1
                        if self.client.interrupt_count >= 2:
                            print("\n第二次键盘中断，程序将退出。")
                            raise
                        print(f"\n捕获到键盘中断。正在重试 (尝试 {attempt + 1}/{retries})... 再次按下 Ctrl+C 可强制退出。")
                        last_exception = sys.exc_info()
                        time.sleep(1) # Short delay for interrupt retry
                        
                    except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout) as e:
                        self.client.interrupt_count = 0 # Reset on other errors
                        wait_time = 2 ** attempt
                        print(f"请求因网络错误失败: {e}。将在 {wait_time} 秒后重试 (尝试 {attempt + 1}/{retries})...")
                        last_exception = sys.exc_info()
                        time.sleep(wait_time)
                        
                    except Exception as e:
                        self.client.interrupt_count = 0
                        # For other exceptions, do not retry.
                        raise Exception(f"请求因不可重试的错误而失败: {str(e)}")

                print("所有重试均告失败。")
                if last_exception:
                    # Re-raise the last captured exception with its original traceback
                    raise last_exception[0].with_traceback(last_exception[1], last_exception[2])
                
                raise Exception("请求在所有重试后失败，但没有捕获到具体异常。")
                    
            def _parse_response(self, data):
                class Response:
                    def __init__(self, data):
                        self.choices = [self.Choice(c) for c in data.get('choices', [])]
                        self.model = data.get('model')
                        self.usage = data.get('usage')
                        
                    class Choice:
                        def __init__(self, choice_data):
                            self.message = self.Message(choice_data.get('message', {}))
                            self.finish_reason = choice_data.get('finish_reason')
                            
                        class Message:
                            def __init__(self, msg_data):
                                self.content = msg_data.get('content')
                                self.role = msg_data.get('role')
                                
                return Response(data)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the simple OpenAI client.")
    parser.add_argument("--api-key", help="OpenAI API Key (overrides OPENAI_API_KEY env var)")
    parser.add_argument("--base-url", help="OpenAI Base URL (overrides OPENAI_BASE_URL env var)")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="Model to use")
    parser.add_argument("--prompt", default="Say hello world", help="Prompt to send")
    
    args = parser.parse_args()
    
    print("Initializing client...")
    try:
        # This will use args if provided, otherwise fallback to env vars
        client = OpenAI(api_key=args.api_key, base_url=args.base_url)
    except ValueError as e:
        print(f"Error initializing client: {e}")
        print("Please provide an API key via --api-key or OPENAI_API_KEY environment variable.")
        return

    print(f"Sending request to {client.base_url} using model {args.model}...")
    try:
        response = client.chat.completions.create(
            model=args.model,
            messages=[
                {"role": "user", "content": args.prompt}
            ]
        )
        
        print("\nResponse received:")
        print("-" * 40)
        print(response.choices[0].message.content)
        print("-" * 40)
        if hasattr(response, 'usage') and response.usage:
            print(f"Usage: {response.usage}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    main()
