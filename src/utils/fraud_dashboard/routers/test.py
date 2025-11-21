import google.generativeai as genai
genai.configure(api_key="AIzaSyAKebTnnWsfiL360F_5ektoi_uAq8kFj1I")

for m in genai.list_models():
    print(m.name)
