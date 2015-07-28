casper.test.begin('add_new_project'
                  /*, planned nr of tests, */,  function suite(test) {
    casper.start('http://localhost:5000', function() {
        test.assertTextExists('Please log in',
                              'Authentication displayed on index page');
        this.test.assertExists('form.login-form', 'Login form found');
        this.fill('form.login-form', {
            'login': 'testhandle@test.com',
            'password':  'TestPass15'
        }, true);
    });
    casper.then(function(){
        test.assertTextExists('ML Time-Series', 'Loaded post-auth index page');
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
        test.assertTextExists('New project successfully created',
                              'Successfully created new project');
    });
    casper.run(function() {
        test.done();
    });
});
