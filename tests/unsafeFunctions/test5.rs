// Unsafe function call as function parameter

fn main() {
	tester(newTester());
}
	
fn tester(x: u16) {
	x;
}

unsafe fn newTester() {
	1;
}
