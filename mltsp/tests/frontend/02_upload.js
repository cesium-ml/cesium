casper.test.begin('upload', function suite(test) {
    casper.start('http://localhost:5000', function() {
        this.page.viewportSize = { width: 1920, height: 1080 };


        casper.setFilter("page.confirm", function(message) {
            this.echo(message);
            return message === "Delete selected project?" ? true : false;
        });


        casper.then(function(){
            casper.waitForSelector("#upload_button", function(){
                this.click("#uploadTabButton");
            });
        });
        casper.then(function(){
            this.evaluate(function() {
                document.querySelector('#upload_project_name_select').selectedIndex = 0;
                document.querySelector('#sep').selectedIndex = 0;
            });
        });
        casper.then(function(){
            this.fill('#uploadForm', {
                'dataset_name': 'test_dataset'
            }, false);
            this.page.uploadFile('#headerfile',
                                 'mltsp/tests/data/asas_training_subset_classes.dat');
            this.page.uploadFile('#zipfile',
                                 'mltsp/tests/data/asas_training_subset.tar.gz');


            var disabled = this.evaluate(function(){
                upload_form_validation();

                if($("#upload_button").is(':disabled')){
                    return true;
                }else{
                    return false;
                }
            });

            if(disabled === true){
                this.echo("the button is disabled!!");
            }else{
                this.echo("button not disabled");
            }

            this.wait(1000, function(){
                this.click("#upload_button");
                this.echo("Clicked #upload_button");
            });

        });

        casper.then(function(){
            casper.waitForText(
                "Upload complete",
                function(){
                    test.assertTextExists("Upload complete");
                },
                function(){
                    test.assertTextExists("Upload complete");
                },
                30000);
        });


    });

    casper.run(function() {
        test.done();
    });
});
