#!/usr/local/bin/perl -w

$first = "";
$n = 0;
open( IN, "awac.6297.xml" );
open( OUT, ">$n.out" );

while( $in = <IN> ) {
  if ( $first eq "" ) { $first = $in; }
  if ( $in =~ m/<VarAsciiFrame/ ) {
     print OUT "    </Instrument>\n";
     close( OUT );
     $n++;
     open( OUT, ">$n.out" );
     print OUT $first;
  }
  print OUT $in;
}

close( OUT );
close( IN );
