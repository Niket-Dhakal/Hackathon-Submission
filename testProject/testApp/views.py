from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import os
from dotenv import load_dotenv, dotenv_values
from .models import UserSearchInfo
# from django.urls import reverse  # Import reverse
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document


current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '..', 'testProject', 'static', '.env')
load_dotenv(dotenv_path=env_path)
MY_API = os.getenv("MY_API_KEY")
os.environ["OPENAI_API_KEY"] = MY_API

def loadMainPage(request):
    return render(request, "index.html")

def getArticles(searchTopic: str, region: str) -> list:
    import requests
    from bs4 import BeautifulSoup


    # Sets up the urls for original bbc search
    searchTopic = f"{searchTopic} located in {region}"
    baseUrl = f"https://www.bbc.co.uk/search?q={searchTopic}"


    # Makes the request to the site, as and then uses beautiful soup to parse through the html
    bbc_page_request = requests.get(baseUrl)
    bbc_page_soup = BeautifulSoup(bbc_page_request.text, "html.parser")


    # Takes all the a elements (links to other articles) and puts it in a temp list
    all_links = bbc_page_soup.find_all("a", class_="ssrcss-1yagzb7-PromoLink exn3ah95")
    all_links_final_list = []


    # Filters all the a tags into just the link
    for link in all_links:
        all_links_final_list.append(link.attrs["href"])


    # Cycles through all of the sites from the final list, and scrapes for all of their articles
    all_articles = []
    for article_link in all_links_final_list:
        bbc_page_url = article_link

        page = requests.get(bbc_page_url)
        page_soup = BeautifulSoup(page.text, "html.parser")

        page_article = ""

        article = page_soup.find_all("div", attrs={"data-component": "text-block"})

        for div in article:
            try:
                if div.attrs["data-component"] == "text-block":
                    page_article += div.text
            except KeyError:
                pass

        all_articles.append(page_article)

    return all_articles, searchTopic

def submit_vocab(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) # data is coming as JSON
            vocab_term = data.get('vocab_term')
            region = data.get('region')

            # Check for missing fields
            if not vocab_term or not region:
                return JsonResponse({'error': 'Missing data'}, status=400)

            term = UserSearchInfo.objects.create(vocabularyTerm=vocab_term, searchRegion=region)
            # object = UserSearchInfo.objects.get(pk=1)

            articles, query = getArticles(vocab_term, region)

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.5,
                max_tokens=None,
                timeout=None,
                max_retries=2
            )

            docs = [Document(page_content=article) for article in articles] # Changed from articles

            # Create the embedding object
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            chunk_embeddings = embeddings.embed_documents([doc.page_content for doc in docs])

            vector_store = InMemoryVectorStore(embeddings)
            ids = vector_store.add_documents(docs)
            
            contexts = "\n\n".join(article for article in articles)

            user_message = f"""\
            CONTEXTS:
            {contexts}

            QUESTION:
            {query}. Make sure to only give normal text.

            ANSWER:
            """

            messages = [
                ("system", "You are a helpful assistant"),
                ("user", user_message)
            ]

            response = llm.invoke(messages)
            llm_response = response.content

            # Deleting the database object
            term.delete()


            # Return the LLM response in the JSON response
            return JsonResponse({'status': 'success', 'llm_response': llm_response})

        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        except Exception as e:
            print("Unexpected error:", e)
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400) #  Important:  Handle non-POST

def success_page(request):
    """
    View for the success page.
    """
    return render(request, 'success.html')