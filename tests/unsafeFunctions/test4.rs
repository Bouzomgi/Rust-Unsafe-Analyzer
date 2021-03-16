// Unsafe variable assignment to unsafe function call

fn main() {
	let x = tester();
}
	
unsafe fn tester() {
	1;
}

