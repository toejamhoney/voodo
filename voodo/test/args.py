def foo(*args, **kwargs):
    print 'args', type(args), ':', args
    print 'kwargs', type(kwargs), ':', kwargs
    try:
        print ','.join(*args)
    except TypeError:
        print 'TypeError',args
    print kwargs.get('k3')


print '-'*80
print 'List'
args = [ 'l', 'i', 's', 't' ]
foo(args)
print '-'*80

print '-'*80
print 'String'
args = 'string'
foo(args)
print '-'*80

print '-'*80
print 'Tuple'
args = ( 'tu', 'ple' )
foo(args)
print '-'*80

print '-'*80
print 'None'
args = None
foo(args)
print '-'*80

print '-'*80
print 'Dict'
args = [ 'a1', { 'k1':'v2', 'k2':'v2' } ]
foo(*args)
print '-'*80

print '-'*80
print 'Kwargs test'
foo(k1='v1', k2='v2')
print '-'*80
