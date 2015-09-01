casper.test.begin('create new project'
                  /*, planned nr of tests, */,  function suite(test) {
    casper.start('http://localhost:5000', function() {

        if(this.exists('form.login-form')){
            this.fill('form.login-form', {
                'login': 'testhandle@test.com',
                'password':  'TestPass15'
            }, true);
        }

        casper.then(function(){
            casper.waitForText("ML Time-Series Platform", function(){
                test.assertTextExists('ML Time-Series Platform',
                                      'Loaded post-auth index page');
            });
        });
        casper.then(function(){
            this.fill('form#newProjectForm', {
                'new_project_name': 'test_name',
                'project_description': 'desc',
                'addl_authed_users': ''
            }, true);
            this.click('#new_project_button');
        });
        casper.then(function(){
            casper.waitForText("New project successfully created",
                               function(){
            test.assertTextExists('New project successfully created',
                                  'Successfully created new project');
                               },
                               function(){
            test.assertTextExists('New project successfully created',
                                  'Successfully created new project');
                               },
                               5000);
        });
    });
    casper.run(function() {
        test.done();
    });
});
