#!/usr/bin/perl
use strict;
use warnings;
open(IN, "$ARGV[0]") or die "cannot open file $ARGV[0]:$!\n";
my %Gene;
while(<IN>){
	chomp;
	my @a=split("\t", $_);
	$Gene{"$a[0]\t$a[1]"} ="$_";
}
close IN;
open(IN, "$ARGV[1]") or die "cannot open file $ARGV[1]:$!\n";
while(<IN>){
	chomp;
	if($_=~/^Hugo/ or $_ =~ /^#version/){
		print "$_\n";
		next;
	}
	my @line = split("\t", $_);
	if(not exists $Gene{"$line[0]\t$line[17]"}){
		print "$_\n";
	}	
}

close IN;
