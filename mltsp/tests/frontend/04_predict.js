casper.test.begin('predict', function suite(test) {
    casper.start('http://localhost:5000', function() {
        this.page.viewportSize = { width: 1920, height: 1080 };

        if(this.exists('form.login-form')){
            this.fill('form.login-form', {
                'login': 'testhandle@test.com',
                'password':  'TestPass15'
            }, true);
        }

        // Predict
        casper.then(function(){
            this.click("#predictTabButton");

            this.evaluate(function() {
                document.querySelector('#prediction_project_name').selectedIndex = 0;
                document.querySelector('#prediction_model_name_and_type').selectedIndex = 0;
                document.querySelector('#newpred_file_sep').selectedIndex = 0;
                return true;
            });

            // UPLOAD FILE(S)
            this.page.uploadFile('#newpred_file',
                                 'mltsp/tests/data/dotastro_215153.dat');

        });

        casper.then(function(){
            var disabled = this.evaluate(function(){
                prediction_metadata_required_validate(false);

                if($("#predict_form_submit_button").is(':disabled')){
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
            //this.page.render("/tmp/test.jpeg", {format: "jpeg"});

            this.click('#predict_form_submit_button');
        });

        casper.then(function(){
            casper.waitForText("This process is currently running", function(){
                test.assertTextExists("This process is currently running",
                                      "Process started");
            });
        });
        casper.then(function(){
            casper.waitForText(
                "Featurization and prediction complete.",
                function(){
                    test.assertTextExists("Featurization and prediction complete.",
                                          "Prediction completed");
                },
                function(){
                    test.assertTextExists("Featurization and prediction complete.",
                                          "Prediction completed");
                },
                10000);
        });


    });

    casper.run(function() {
        test.done();
    });
});
