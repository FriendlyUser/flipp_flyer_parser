# flipp grocery scrapper

My original plan with this script was to get lots of grocery data to analyze and parse, but after realising that the cost of items can vary from store to store, will modify the script in order to track differences between stores.

https://friendlyuser.github.io/posts/flipp_grocery_scrapper


## How to Use

In order to use these scripts, you may need advanced web knowledge for loblaws and superstore, I recommend installing an extension that can read
cookies for the last_store_visited and flipp-store-code_2271

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