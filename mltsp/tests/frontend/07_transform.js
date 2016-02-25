casper.test.begin('transform', function suite(test) {
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
                document.querySelector('#transform_data_project_name_select').selectedIndex = 0;
                document.querySelector('#transform_data_dataset_select').selectedIndex = 0;
                document.querySelector('#transform_data_transform_select').selectedIndex = 0;
            });
        });
        this.wait(1000, function(){
            this.click("#transform_data_button");
            this.echo("Clicked #transform_data_button");
        });

        casper.then(function(){
            casper.waitForText(
                "Transformation complete",
                function(){
                    test.assertTextExists("Transformation complete");
                },
                function(){
                    test.assertTextExists("Transformation complete");
                },
                30000);
        });


    });

    casper.run(function() {
        test.done();
    });
});
