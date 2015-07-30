casper.test.begin('build model', function suite(test) {
    casper.start('http://localhost:5000', function() {
        this.page.viewportSize = { width: 1920, height: 1080 };

        // Build model
        casper.then(function(){

            this.evaluate(function() {
                document.querySelector('#buildmodel_project_name_select').selectedIndex = 0;
                document.querySelector('#modelbuild_featset_name_select').selectedIndex = 0;
                document.querySelector('#model_type_select').selectedIndex = 0;
                build_model_form_validation();
                return true;
            });
            this.click('#model_build_submit_button');
        });

        casper.then(function(){
            casper.waitForText("This process is currently running", function(){
                test.assertTextExists("This process is currently running",
                                      "Process started");
            });
        });
        casper.then(function(){
            casper.waitForText(
                "Model creation complete.",
                function(){
                    test.assertTextExists("Model creation complete.",
                                          "Model building completed");
                },
                function(){
                    test.assertTextExists("Model creation complete.",
                                          "Model building completed");
                },
                10000);
        });

    });

    casper.run(function() {
        test.done();
    });
});
