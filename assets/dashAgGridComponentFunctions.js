var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.unix_to_str = function (props) {

    return React.createElement(
        'span', {},
        new Intl.DateTimeFormat('en-GB', {
            dateStyle: 'medium',
            timeStyle: 'long',
            timeZone: 'Europe/London',
        }).format(props.value * 1000)
    );
};

dagcomponentfuncs.des_result_link = function (props) {
    if (props.value == '') {
        return ''
    }
    return React.createElement(
        'a',
        { href: 'des/result/' + props.value },
        'Result'
    );
};