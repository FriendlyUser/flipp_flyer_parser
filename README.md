# flipp grocery scrapper

My original plan with this script was to get lots of grocery data to analyze and parse, but after realising that the cost of items can vary from store to store, will modify the script in order to track differences between stores.

https://friendlyuser.github.io/posts/flipp_grocery_scrapper

Ideally you would feed this data into a gpt or equivalent to get items of interest.

For example

https://chat.openai.com/share/c1288cbf-8890-4833-a87c-8601cb065d5a


## Making a database

For postgres

```
CREATE TABLE grocery (
  label varchar(255),
    flyer_path varchar(255),
      product_name varchar(255),
        data_product_id varchar(100),
          savings varchar(255),
            current_price decimal(10,2),
              start_date timestamp,
                end_date timestamp,
                  description varchar(255),
                    size varchar(255),
                      quantity varchar(255),
                        product_type varchar(100),
                          frozen boolean,
                            see_more_link varchar(255)
                            );)
```

To halt duplicates
```
ALTER TABLE grocery 
ADD CONSTRAINT grocery_unique_flyer_see_more_label 
UNIQUE (flyer_path, see_more_link, label);
```