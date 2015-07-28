casper.test.begin('main_pipeline', function suite(test) {
    casper.start('http://localhost:5000', function() {
        this.page.viewportSize = { width: 1920, height: 1080 };
        test.assertTextExists('Please log in',
                              'Authentication displayed on index page');
        this.test.assertExists('form.login-form', 'Login form found');
        this.fill('form.login-form', {
            'login': 'testhandle@test.com',
            'password':  'TestPass15'
        }, true);

        casper.setFilter("page.confirm", function(message) {
            this.echo(message);
            return message === "Delete selected project?" ? true : false;
        });

        // Fill form and click submit button
        casper.then(function(){
            this.fill('form#newProjectForm', {
                'new_project_name': 'test_name',
                'project_description': 'desc',
                'addl_authed_users': ''
            }, false);
            this.click('#new_project_button');
        });

        // Assert pop-up dialog exists with success message & click ok
        casper.then(function() {
            casper.waitForSelector("#new-project-dialog-ok-btn", function(){
                test.assertTextExists('New project successfully created',
                                      'Successfully created new project');
                this.click('#new-project-dialog-ok-btn');
            });
        });

        // Wait for page to reload & delete new project
        casper.then(function(){
            casper.waitForSelector("#featurize_button", function(){
                this.click("#featurizeTabButton");
            });
        });
        casper.then(function(){
            this.evaluate(function() {
                document.querySelector('#featureset_project_name_select').selectedIndex = 0;
                document.querySelector('#sep').selectedIndex = 0;
            });
        });
        casper.then(function(){
            this.fill('#featurizeForm', {
                'featureset_name': 'test_featset'
            }, false);
            this.page.uploadFile('#headerfile',
                                 'mltsp/tests/data/asas_training_subset_classes.dat');
            this.page.uploadFile('#zipfile',
                                 'mltsp/tests/data/asas_training_subset.tar.gz');


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
            //this.page.render("/tmp/test.jpeg", {format: "jpeg"});

            this.wait(1000, function(){
                this.click("#featurize_button");
                this.echo("Clicked #featurize_button");

                this.evaluate(function(){
                    featurizeFormSubmit();
                });
            });

        });

        casper.then(function(){
            casper.waitForText("This process is currently running", function(){
                test.assertTextExists("This process is currently running",
                                      "Featurization process started");
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


        // Delete new project
        casper.then(function(){

            this.evaluate(function() {
                document.querySelector('#action').selectedIndex = 1;
                document.querySelector('#PROJECT_NAME_TO_EDIT').selectedIndex = 0;
                return true;
            });
            this.click('#editOrDeleteSubmit');
        });

        casper.then(function(){
            casper.waitForSelector("#editDeleteResultsDialog-okbtn", function(){
                test.assertTextExists('Deleted 1 project(s).',
                                      'Got success message (in jQuery dialog)');
                this.click("#editDeleteResultsDialog-okbtn");
            });
        });




    });

    casper.run(function() {
        test.done();
    });
});
