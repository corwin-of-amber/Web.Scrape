
from construct import *


class F4F:
    Box = Struct("Box",
                 UBInt32("size"),
                 Bytes("type", 4),
                 Bytes("data", lambda ctx: ctx.size-8))
    
    Box = Struct("Box",
                 UBInt32("size"),
                 Bytes("type", 4),
                 Switch("body", lambda ctx: ctx['type'],
                        {'abst':
                            Struct("abst",
                                   Bytes("metadata", 29),
                                   Padding(5),
                                   Byte("num_seg_tables"),
                                   Array(lambda ctx: ctx.num_seg_tables, Rename("seg_tables", Box)),
                                   Byte("num_frag_tables"),
                                   Array(lambda ctx: ctx.num_frag_tables, Rename("frag_tables", Box)),
                                   Anchor('b'),
                                   Bytes("data", lambda ctx: ctx._['size']-ctx.b)
                                   )
                         }, default=
                            Bytes("data", lambda ctx: ctx.size-8))
                 )

    Fragment = Struct("Fragment",
                      Rename("header", Box),
                      Rename("header2", Box),
                      Field("buf", 160)
                      )
                      #Rename("buf", CStringAdapter(GreedyRange(Field(None, 1)))))


if __name__ == '__main__':
    sample = open("/tmp/mako_hd/Seg1-Frag1").read()
    print F4F.Fragment.parse(sample)