import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil import parser
import isodate

# Function to fetch channel statistics
def get_channel_stats(youtube, channel_ids):
    all_data = []

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=','.join(channel_ids)
    )
    response = request.execute()

    for item in response['items']:
        data = {'channelName': item['snippet']['title'],
                'subscribers': item['statistics']['subscriberCount'],
                'views': item['statistics']['viewCount'],
                'videos': item['statistics']['videoCount'],
                'playlistId': item['contentDetails']['relatedPlaylists']['uploads']
                }
        all_data.append(data)

    return pd.DataFrame(all_data)

# Function to fetch video statistics
def get_video_stats(youtube, playlist_id):
    video_ids = []

    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    while next_page_token is not None:
        request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')

    return video_ids

# Function to fetch video details
def get_video_details(youtube, video_ids):
    all_video_info = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i + 50])
        )
        response = request.execute()

        for video in response['items']:
            stats_to_keep = {'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                             'statistics': ['viewCount', 'likeCount', 'favoriteCount', 'commentCount'],
                             'contentDetails': ['duration', 'definition', 'caption']
                             }
            video_info = {}
            video_info['video_id'] = video['id']

            for k in stats_to_keep.keys():
                for v in stats_to_keep[k]:
                    try:
                        video_info[v] = video[k][v]
                    except:
                        video_info[v] = None

            all_video_info.append(video_info)

    return pd.DataFrame(all_video_info)

# Function to convert object type to numeric type
def convert_to_numeric(df):
    numeric_cols = ['viewCount', 'likeCount', 'commentCount']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce', axis=1)
    return df

# Function for date conversion
def convert_dates(df):
    df['publishedAt'] = df['publishedAt'].apply(lambda x: parser.parse(x))
    df['publishedDay'] = df['publishedAt'].apply(lambda x: x.strftime("%A"))
    return df

# Function for time to seconds conversion
def convert_time_to_seconds(df):
    df['videoDuration'] = df['duration'].apply(lambda x: isodate.parse_duration(x).total_seconds())
    return df

# Function to get tag count
def get_tag_count(df):
    df['tagCount'] = df['tags'].apply(lambda x: 0 if x is None else len(x))
    return df

# Function for top performing videos by views
def top_videos_by_views(df):
    top_videos = df.sort_values('viewCount', ascending=False).head(9)
    plt.figure(figsize=(10, 6))
    plt.bar(top_videos['title'], top_videos['viewCount'], color='skyblue')
    plt.xticks(rotation=90)
    plt.xlabel('Video Title')
    plt.ylabel('View Count')
    plt.title('Top Performing Videos by Views')
    st.pyplot()

# Function for lowest performing videos by views
def low_videos_by_views(df):
    low_videos = df.sort_values('viewCount', ascending=True).head(9)
    plt.figure(figsize=(10, 6))
    plt.bar(low_videos['title'], low_videos['viewCount'], color='skyblue')
    plt.xticks(rotation=90)
    plt.xlabel('Video Title')
    plt.ylabel('View Count')
    plt.title('Lowest Performing Videos by Views')
    st.pyplot()

# Function for distribution of view counts by channel
def view_count_distribution(df):
    plt.figure(figsize=(10, 6))
    for channel, data in df.groupby('channelTitle'):
        plt.hist(data['viewCount'], bins=30, alpha=0.5, label=channel, density=True)
    plt.xlabel('View Count')
    plt.ylabel('Density')
    plt.title('View Count Distribution by Channel')
    plt.legend()
    st.pyplot()

# Function for duration of videos
def video_duration_distribution(df):
    plt.figure(figsize=(10, 6))
    plt.hist(df['videoDuration'], bins=30, color='green', alpha=0.7, edgecolor='black')
    plt.xlabel('Video Duration (seconds)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Video Durations')
    st.pyplot()

# Function for day-wise video publishing frequency
def publishing_frequency(df):
    day_counts = df['publishedDay'].value_counts().sort_index()
    plt.figure(figsize=(10, 6))
    day_counts.plot(kind='bar', color='purple')
    plt.xlabel('Day of the Week')
    plt.ylabel('Number of Videos Published')
    plt.title('Videos Published by Day of the Week')
    plt.xticks(rotation=45)
    st.pyplot()

# Main function to run the Streamlit app
def main():
    st.title('InsightTube')

    # User input for channel ID
    st.sidebar.title('Welcome to Youtube Analytics Page!')
    channel_id = st.text_input('Enter YouTube Channel ID:')
    if st.button('Generate Analytics'):
        if channel_id:
            # Initialize YouTube API
            api_key = 'AIzaSyCNk0FmDv63Desj4ytM2kbHTkIwwXHeOa4'
            youtube = build("youtube", "v3", developerKey=api_key)

            # Fetch channel statistics
            channel_stats = get_channel_stats(youtube, [channel_id])

            if not channel_stats.empty:
                st.subheader('Channel Statistics')
                st.write(channel_stats)

                # Fetch video statistics
                video_ids = get_video_stats(youtube, channel_stats.iloc[0]['playlistId'])
                video_set = get_video_details(youtube, video_ids)

                # Data preprocessing
                video_set = convert_to_numeric(video_set)
                video_set = convert_dates(video_set)
                video_set = convert_time_to_seconds(video_set)
                video_set = get_tag_count(video_set)

                st.subheader('Channel Analysis')
                st.write(video_set)

                st.set_option('deprecation.showPyplotGlobalUse', False)
                # Display analytics
                st.subheader('Top Performing Videos by Views')
                top_videos_by_views(video_set)

                st.subheader('Lowest Performing Videos by Views')
                low_videos_by_views(video_set)

                st.subheader('View Count Distribution by Channel')
                view_count_distribution(video_set)

                st.subheader('Distribution of Video Durations')
                video_duration_distribution(video_set)

                st.subheader('Videos Published by Day of the Week')
                publishing_frequency(video_set)

            else:
                st.error('Channel ID not found or no data available.')

# Run the app
if __name__ == '__main__':
    main()
