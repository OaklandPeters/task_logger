from review import Reviewer, review, pluck


if __name__ == "__main__":

    #
    enami = {
        'name':'enami', 
        'directory':"/data/htdocs/cccid/build/compounds-db/data-files/enami/",
        'log':"/data/htdocs/cccid/build/compounds-db/data-files/enami/awk-sourcedata-insertion-log.json",
    }
    
    Reviewer(**enami)
    
    print("Left reviewer....")