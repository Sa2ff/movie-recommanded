import streamlit as st
import pandas as pd
import pickle
import requests

def fetch_poster(movie_id):
    api_key = "fc9636436238379b763e5f4e8e734d60"  # Replace with your valid API key
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    data = requests.get(url)
    
    if data.status_code == 200:
        poster_path = data.json().get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
    elif data.status_code == 401:  # Unauthorized
        return "Invalid API Key. Please check your TMDb API key."
    else:
        return "Error fetching image. Please try again later."

# Function to recommend movies based on content-based filtering
def recommend_movies_content(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:11]
    
    recommended_movies = []
    recommended_movie_posters = []
    
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        movie_title = movies.iloc[i[0]].title
        
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movies.append(movie_title)
    
    return recommended_movies, recommended_movie_posters

# Function to recommend movies based on collaborative filtering
def recommend_movies_collaborative(movie):
    movie_id = movies[movies['title'] == movie].movie_id.values[0]
    similar_movies = ratings[ratings['movieId'] == movie_id].sort_values(by='rating', ascending=False).head(10)
    
    recommended_movies = []
    recommended_movie_posters = []
    
    for _, row in similar_movies.iterrows():
        movie_title = movies[movies['movie_id'] == row['movieId']]['title'].values[0]
        recommended_movies.append(movie_title)
        recommended_movie_posters.append(fetch_poster(row['movieId']))
    
    return recommended_movies, recommended_movie_posters

# Function to combine recommendations
def hybrid_recommendations(movie):
    content_movies, content_posters = recommend_movies_content(movie)
    collaborative_movies, collaborative_posters = recommend_movies_collaborative(movie)

    # Combine unique recommendations from both methods
    all_recommended_movies = list(set(content_movies + collaborative_movies))
    all_recommended_posters = []

    for title in all_recommended_movies:
        if title in content_movies:
            index = content_movies.index(title)
            all_recommended_posters.append(content_posters[index])
        else:
            index = collaborative_movies.index(title)
            all_recommended_posters.append(collaborative_posters[index])

    return all_recommended_movies, all_recommended_posters

# Load data correctly
movies_dict = pickle.load(open(r'C:\Users\DELL\movie-recommanded\movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)  # Convert dictionary to DataFrame
similarity = pickle.load(open(r'C:\Users\DELL\movie-recommanded\similarity.pkl', 'rb'))
ratings = pd.read_csv(r'C:\Users\DELL\movie-recommanded\ratings_small.csv.zip')

# Streamlit UI setup
st.title('🎬 Movie Recommender System')

# Search box for movie selection
search_term = st.text_input('Search for a movie:')
if search_term:
    filtered_movies_search = movies[movies['title'].str.contains(search_term, case=False)]
else:
    filtered_movies_search = movies

if not filtered_movies_search.empty:
    selected_movi = st.selectbox('Select a movie', filtered_movies_search['title'].values)

    if st.button('Recommend'):
        if selected_movi not in movies['title'].values:
            st.error("There is no such movie in our list.")
        else:
            with st.spinner('Fetching recommendations...'):
                try:
                    recommended_movies, recommended_movie_posters = hybrid_recommendations(selected_movi)
                    st.subheader(f'Movies similar to **{selected_movi}**')
                    
                    # Display the selected movie 
                    selected_movie_id = movies[movies['title'] == selected_movi].movie_id.values[0]
                    st.image(fetch_poster(selected_movie_id))

                    # Display recommendations in a grid layout
                    cols_rec = st.columns(5)
                    for i in range(len(recommended_movies)):
                        with cols_rec[i % 5]:
                            st.image(recommended_movie_posters[i])
                            st.text(recommended_movies[i])

                    st.success("Recommendations fetched successfully!")

                except Exception as e:
                    st.error(f"An error occurred: {e}")
else:
    st.warning("No movies found. Please try a different search term.")