import os
import sys
from instaloader import Post, Instaloader
import concurrent.futures
from dotenv import load_dotenv
import pandas as pd


print("시작합니다")
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    CWD = os.path.abspath(os.path.dirname(sys.executable))
    load_dotenv(dotenv_path=os.path.join(CWD, 'config.env'))
    EXCEL_PATH = os.path.join(CWD, "data.xlsx")
else:
    CWD = os.path.abspath(os.path.dirname(sys.executable))
    load_dotenv('config.env')
    EXCEL_PATH = "data.xlsx"
print("환경변수 세팅")

user = os.getenv('INSTA_USERNAME')
passwd = os.getenv('INSTA_PASSWORD')

L = Instaloader()
L.login(user=user,passwd=passwd)

print("인스타그램 로그인: "+user)

class InstaPostInfo:
    def __init__(self, url,shortcode, captions, hashtags, mentions):
        self.url = url
        self.shortcode = shortcode
        if not pd.isna(captions):
            self.captions = captions.split(",")
        else:
            self.captions = None
        if not pd.isna(hashtags):
            self.hashtags = hashtags.split(",")
        else:
            self.hashtags = None
        if not pd.isna(mentions):
            self.mentions = mentions.split(",")
        else:
            self.mentions = None
            
     
    def validate(self):
        is_error = False
        post = Post.from_shortcode(L.context, self.shortcode)
        if self.hashtags:
            for hashtag in self.hashtags:
                if hashtag not in post.caption_hashtags:
                    print(f'{self.shortcode}의 태그 목록에서 \'{hashtag}\' 없습니다')
                    print(f'{self.url}을 확인해주세요')
                    is_error = True
                    break
        if self.mentions:
            for mention in self.mentions:
                if mention not in post.caption_mentions:
                    print(f'{self.shortcode}의 맨션 내용에 \'{mention}\' 없습니다')
                    print(f'{self.url}을 확인해주세요')
                    is_error = True
                    break
        if self.captions:
            for caption in self.captions:
                if caption not in post.caption:
                    print(f'{self.shortcode}의 본문 내용에 \'{caption}\' 없습니다')
                    print(f'{self.url}을 확인해주세요')
                    is_error = True
                    break

        return is_error
    
    def __str__(self):
        return self.shortcode +'\n'+self.url




def main():
    def process_post(insta_post_info: InstaPostInfo):
        is_error =  insta_post_info.validate()
        if is_error:
            error_post_info_list.append(insta_post_info)

    def get_info_list_from_excel():
        df = pd.read_excel(EXCEL_PATH)
        for _, row in df.iterrows():
            if pd.isnull(row['expires_at']):
                raise Exception(f'{row["url"]}에 지정된 유효기간이 없습니다')
            if row['expires_at'] < pd.Timestamp.now():
                continue
            insta_post_info = InstaPostInfo(row['url'],row['shortcode'], row['captions'], row['hashtags'], row['mentions'])
            insta_post_info_list.append(insta_post_info)

    
    insta_post_info_list =[]
    error_post_info_list = []
    get_info_list_from_excel()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_post, insta_post_info_list)


    print('-' * 50)
    print("발견된 오류 포스트 목록 "+ str(len(error_post_info_list)) + "개")
    for error_post_info in error_post_info_list:
        print(error_post_info)
        

if __name__ == '__main__':
    main()