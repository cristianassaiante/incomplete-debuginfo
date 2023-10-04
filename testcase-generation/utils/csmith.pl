#!/usr/bin/perl -w

##################################################################

# https://github.com/csmith-project/csmith/blob/master/src/RandomProgramGenerator.cpp

my @ALL_SWARM_OPTS = (
    "arrays",
    # "checksum",
    "comma-operators",
    "compound-assignment",
    "consts",
    "divs",
    "embedded-assigns",
    "jumps",
    "longlong",
    "force-non-uniform-arrays",
    "math64",
    "muls",
    "packed-struct",
    "paranoid",
    "pointers",
    "structs",
    "volatiles",
    "volatile-pointers",
    "arg-structs",
    "dangling-global-pointers",
   );

my $XTRA = "--no-float --no-checksum --safe-math --no-argc --no-inline-function --no-unions --no-bitfields --no-return-structs --max-funcs 5 --max-block-depth 1";

my $PACK = "";

##################################################################
my $SEED_INFO = "";
if( $#ARGV != -1 ){
    $SEED_INFO="--seed $ARGV[0]";
    srand($ARGV[0])
}

my $SWARM_OPTS = "";
my $p = rand();
foreach my $opt (@ALL_SWARM_OPTS) {
    if (rand() < 0.5) {
        $SWARM_OPTS .= " --$opt ";
    }
    else {
        $SWARM_OPTS .= " --no-$opt ";
    }
}
my $cmd;
$cmd = "csmith $SWARM_OPTS $PACK $SEED_INFO $XTRA";
my $res = (system $cmd);
exit $res;
##################################################################
