casper.test.begin('featurize', function suite(test) {
    casper.start('http://localhost:5000', function() {
        this.page.viewportSize = { width: 1920, height: 1080 };


        casper.setFilter("page.confirm", function(message) {
            this.echo(message);
            return message === "Delete selected project?" ? true : false;
        });


        casper.then(function(){
            casper.waitForSelector("#featurize_button", function(){
                this.click("#featurizeTabButton");
            });
        });
        casper.then(function(){
            this.evaluate(function() {
                document.querySelector('#featureset_project_name_select').selectedIndex = 0;
                document.querySelector('#featureset_dataset_select').selectedIndex = 0;
                document.querySelector('#sep').selectedIndex = 0;
            });
        });
        casper.then(function(){
            this.fill('#featurizeForm', {
                'featureset_name': 'test_featset'
            }, false);

            var disabled = this.evaluate(function(){
                featurize_form_validation();

                if($("#featurize_button").is(':disabled')){
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
                this.click("#featurize_button");
                this.echo("Clicked #featurize_button");
            });

        });

        casper.then(function(){
            casper.waitForText(
                "Featurization of timeseries data complete.",
                function(){
                    test.assertTextExists("Featurization of timeseries data complete.",
                                          "Featurization completed");
                },
                function(){
                    test.assertTextExists("Featurization of timeseries data complete.",
                                          "Featurization completed");
                },
                30000);
        });


    });

    casper.run(function() {
        test.done();
    });
});
