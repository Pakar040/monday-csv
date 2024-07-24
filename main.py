import requests
import pandas as pd
from datetime import datetime


board_ids = [0000000, 0000000, 0000000]
api_key = "XXXXXXXXXXXXXXXXXXXXXXXXX"
api_url = "https://api.monday.com/v2"
headers = {
    'Content-Type': 'application/json',
    'Authorization': api_key,
    'API-Version': '2024-01'
}


def main():

    current_date = datetime.now()
    formatted_date = current_date.strftime("%-m/%-d/%Y")

    json_data_rows = []

    for board_i in range(len(board_ids)):

        initial_query = f"""
            query {{
              boards (ids: {board_ids}){{
                items_page {{
                  cursor
                  items {{
                    name 
                    board {{name}}
                    group {{title}}
                    column_values {{
                      column {{title}}
                      text
                    }}
                    subitems {{
                      name
                      column_values{{
                        column {{title}}
                        text
                      }}
                    }}
                  }}
                }}
              }}
            }}
        """

        json_data = fetch_data(initial_query)
        json_data_rows += process_data(json_data["data"]["boards"][board_i]["items_page"], formatted_date)

        cursor = json_data["data"]["boards"][board_i]["items_page"]["cursor"]

        while cursor is not None:
            next_query = f"""
                query {{
                  next_items_page (cursor: "{cursor}") {{
                    cursor
                    items {{
                      name 
                      board {{name}}
                      group {{title}}
                      column_values {{
                        column {{title}}
                        text
                      }}
                      subitems {{
                        name
                        column_values{{
                          column {{title}}
                          text
                        }}
                      }}
                    }}
                  }}
                }}
            """
            json_data = fetch_data(next_query)
            json_data_rows.extend(process_data(json_data["data"]["next_items_page"], formatted_date))
            cursor = json_data["data"]["next_items_page"]["cursor"]

    df = pd.DataFrame(json_data_rows)
    df.to_csv('data.csv', index=False)


def fetch_data(query):
    response = requests.post(api_url, headers=headers, json={'query': query})
    return response.json()


def process_data(data, date):
    data_rows = []
    for item in data["items"]:
        item_data = {
            'Date Downloaded': date,
            'Item Name': item.get('name'),
            'Board Name': item.get('board', {}).get('name'),
            'Group Title': item.get('group', {}).get('title')
        }
        item_data.update({f"{column.get('column', {}).get('title')} (Item)": column.get('text')
                          for column in item["column_values"]})

        for subitem in item["subitems"]:
            row_of_data = item_data.copy()
            row_of_data['Subitem Name'] = subitem.get('name')
            row_of_data.update({f"{column.get('column').get('title')} (Subitem)": column.get('text')
                                for column in subitem["column_values"]})
            customize_data(row_of_data)
            data_rows.append(row_of_data)
    return data_rows


def customize_data(data):
    time_tracking = data.get('Time Tracking (Subitem)').split(':')
    if len(time_tracking) == 3:
        time_tracking = float(time_tracking[0]) + float(time_tracking[1]) / 60 + float(time_tracking[2]) / 60 / 60
        time_tracking = round(time_tracking, 2)
    else:
        time_tracking = None
    data['Time Tracking (Subitem)'] = time_tracking


if __name__ == "__main__":
    main()
