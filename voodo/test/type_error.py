def foo():
    print 'Foo'

def bar(baz):
    foobar = None
    print baz + foobar

if __name__ == '__main__':
    baz = 'Bar'
    try:
        foo(baz)
    except TypeError as error:
        print repr(error)
        raise error
    except Exception as err2:
        print 'Err2:' + repr(err2)

    try:
        bar(baz)
    except Exception as error:
        print repr(error)
